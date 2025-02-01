"""Test script for RunComfy and ComfyUI API integration"""

import os
import uuid
import asyncio
import httpx
import json
import websockets
from urllib.parse import urlencode
from dotenv import load_dotenv

async def test_comfyui_api():
    print("🚀 Testing ComfyUI API...")
    
    # Generate a unique client ID
    client_id = str(uuid.uuid4())
    print(f"Client ID: {client_id}")
    
    # Use existing ComfyUI URL
    comfyui_url = "https://a06a0eb0-1c8b-4096-a1bf-f5855b3e4ab7-comfyui.runcomfy.com"
    print(f"Using ComfyUI URL: {comfyui_url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Get object info to find available models
            print("\n1️⃣ Getting available models...")
            object_info_url = f"{comfyui_url}/object_info"
            object_info_response = await client.get(object_info_url)
            object_info_response.raise_for_status()
            object_info = object_info_response.json()
            
            # Get available checkpoints
            checkpoints = object_info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [])
            if not checkpoints:
                print("❌ No checkpoints found")
                return
            
            if isinstance(checkpoints[0], list):
                checkpoints = checkpoints[0]
                
            print(f"Found {len(checkpoints)} available checkpoints:")
            for i, ckpt in enumerate(checkpoints[:5], 1):
                print(f"{i}. {ckpt}")
            if len(checkpoints) > 5:
                print(f"...and {len(checkpoints) - 5} more")
            
            # Use the first available checkpoint
            checkpoint_name = checkpoints[0]
            print(f"\nUsing checkpoint: {checkpoint_name}")
            
            # Step 2: Create workflow
            print("\n2️⃣ Creating workflow...")
            workflow = {
                "1": {
                    "inputs": {
                        "ckpt_name": checkpoint_name
                    },
                    "class_type": "CheckpointLoaderSimple"
                },
                "2": {
                    "inputs": {
                        "text": "a photo of a cat",
                        "clip": ["1", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "3": {
                    "inputs": {
                        "text": "bad quality, blurry",
                        "clip": ["1", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "4": {
                    "inputs": {
                        "seed": 42,
                        "steps": 20,
                        "cfg": 8,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1,
                        "model": ["1", 0],
                        "positive": ["2", 0],
                        "negative": ["3", 0],
                        "latent_image": ["5", 0]
                    },
                    "class_type": "KSampler"
                },
                "5": {
                    "inputs": {
                        "width": 512,
                        "height": 512,
                        "batch_size": 1
                    },
                    "class_type": "EmptyLatentImage"
                },
                "6": {
                    "inputs": {
                        "samples": ["4", 0],
                        "vae": ["1", 2]
                    },
                    "class_type": "VAEDecode"
                },
                "7": {
                    "inputs": {
                        "filename_prefix": "test_output",
                        "images": ["6", 0]
                    },
                    "class_type": "SaveImage"
                }
            }
            
            # Step 3: Queue the prompt
            print("\n3️⃣ Queueing prompt...")
            prompt_data = {
                "prompt": workflow,
                "client_id": client_id
            }
            
            prompt_response = await client.post(
                f"{comfyui_url}/prompt",
                json=prompt_data
            )
            prompt_response.raise_for_status()
            prompt_result = prompt_response.json()
            prompt_id = prompt_result.get("prompt_id")
            print(f"✅ Prompt queued: {prompt_result}")
            
            if prompt_id:
                # Step 4: Monitor progress via WebSocket
                print("\n4️⃣ Monitoring progress...")
                ws_url = f"wss://{comfyui_url.split('://')[-1]}/ws?clientId={client_id}"
                print(f"Connecting to WebSocket: {ws_url}")
                
                async with websockets.connect(ws_url) as websocket:
                    while True:
                        try:
                            message = await websocket.recv()
                            print(f"Progress update: {message}")
                            
                            # Check if generation is complete
                            if '"type": "executing"' in message and '"node": null' in message:
                                print("✅ Generation complete!")
                                break
                        except websockets.exceptions.ConnectionClosed:
                            print("WebSocket connection closed")
                            break
                
                # Step 5: Get results from history
                print("\n5️⃣ Getting results...")
                history_url = f"{comfyui_url}/history/{prompt_id}"
                history_response = await client.get(history_url)
                history_response.raise_for_status()
                history = history_response.json()
                
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    print("\nOutputs available:")
                    
                    # Create output directory if it doesn't exist
                    os.makedirs("output", exist_ok=True)
                    
                    # Download all media outputs
                    for node_id, node_output in outputs.items():
                        # Download images
                        if "images" in node_output:
                            for image in node_output["images"]:
                                filename = image.get("filename")
                                subfolder = image.get("subfolder", "")
                                temp = image.get("type", "output")
                                
                                params = {
                                    "filename": filename,
                                    "subfolder": subfolder,
                                    "type": temp
                                }
                                url = f"{comfyui_url}/view?{urlencode(params)}"
                                print(f"Downloading image: {filename}")
                                
                                image_response = await client.get(url)
                                image_response.raise_for_status()
                                
                                output_path = os.path.join("output", filename)
                                with open(output_path, "wb") as f:
                                    f.write(image_response.content)
                                print(f"✅ Saved to: {output_path}")
                else:
                    print("❌ No outputs found in history")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if hasattr(e, "response"):
                print(f"Response: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(test_comfyui_api())
