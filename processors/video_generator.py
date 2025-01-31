from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
import ffmpeg
from typing import List
import asyncio
import os

async def create_video_segments(image_paths: List[str], audio_paths: List[str]) -> List[str]:
    """Create final video segments with zoom effects."""
    
    video_paths = []
    for i, (image_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
        output_path = f"temp/segment_{i}.mp4"
        
        # Create video with zoom effect
        stream = ffmpeg.input(image_path)
        
        # Add zoom effect
        stream = ffmpeg.filter(stream, 'zoompan',
            z='min(zoom+0.0015,1.5)',
            d=60,
            x='iw/2-(iw/zoom/2)',
            y='ih/2-(ih/zoom/2)'
        )
        
        # Scale to 9:16
        stream = ffmpeg.filter(stream, 'scale', 1080, 1920)
        
        # Add audio
        audio = ffmpeg.input(audio_path)
        
        # Output final video
        stream = ffmpeg.output(stream, audio, output_path,
            acodec='aac',
            vcodec='libx264',
            pix_fmt='yuv420p',
            r=30
        )
        
        await asyncio.create_subprocess_exec(
            'ffmpeg',
            *stream.get_args(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        video_paths.append(output_path)
    
    return video_paths 