from elevenlabs import generate, set_api_key
import os
from typing import List
import asyncio

async def generate_voiceovers(segments: List[str], voice_id: str) -> List[str]:
    """Generate voiceovers using ElevenLabs API."""
    
    set_api_key(os.getenv("ELEVEN_LABS_API_KEY"))
    
    audio_paths = []
    for i, segment in enumerate(segments):
        # Generate audio
        audio = generate(
            text=segment,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )
        
        # Save audio file
        audio_path = f"temp/audio_{i}.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio)
        audio_paths.append(audio_path)
        
        await asyncio.sleep(1)  # Rate limiting
    
    return audio_paths 