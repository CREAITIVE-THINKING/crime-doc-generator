import os
import asyncio
from typing import List
import requests
from pathlib import Path
import openai

async def generate_sd_prompts(segment: str, client) -> str:
    """Generate Stable Diffusion prompt for a segment."""
    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": """You are a Stable Diffusion prompt engineer.
            Create detailed prompts that will generate consistent, dramatic true crime documentary scenes.
            Focus on mood, lighting, and composition."""},
            {"role": "user", "content": f"Create a cinematic SD prompt for this scene: {segment}"}
        ]
    )
    return response.choices[0].message.content

async def generate_images(segments: List[str], character_image_path: str) -> List[str]:
    """Generate images using RunComfy API."""
    
    api_key = os.getenv("RUNCOMFY_API_KEY")
    user_id = os.getenv("RUNCOMFY_USER_ID")
    
    image_paths = []
    for i, segment in enumerate(segments):
        # Generate prompt
        prompt = await generate_sd_prompts(segment, openai.AsyncOpenAI())
        
        # Launch RunComfy job
        response = requests.post(
            "https://api.runcomfy.com/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, bad composition",
                "width": 1080,
                "height": 1920,
                "character_reference": character_image_path
            }
        )
        
        # Save generated image
        image_path = f"temp/image_{i}.png"
        with open(image_path, "wb") as f:
            f.write(requests.get(response.json()["image_url"]).content)
        image_paths.append(image_path)
        
        await asyncio.sleep(1)  # Rate limiting
    
    return image_paths 