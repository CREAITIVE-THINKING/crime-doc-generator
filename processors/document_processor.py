from pathlib import Path
import os
from typing import List
import asyncio
from openai import AsyncOpenAI
from PyPDF2 import PdfReader
import io
import contextlib

class OpenAIClient:
    """Singleton wrapper for OpenAI client to ensure proper cleanup"""
    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._client

    def __init__(self):
        if OpenAIClient._client is None:
            # Initialize without any proxy settings
            OpenAIClient._client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url="https://api.openai.com/v1"
            )

async def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text content from PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                try:
                    pdf_reader.decrypt('')  # Try empty password first
                    print(f"Successfully decrypted {file_path}")
                except:
                    raise Exception(f"Could not decrypt PDF: {file_path}")
                    
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
                
            if not text.strip():
                raise Exception(f"No text could be extracted from PDF: {file_path}")
                
            return text
    except Exception as e:
        raise Exception(f"Error processing PDF {file_path}: {str(e)}")

async def process_documents(file_paths: List[Path]) -> List[str]:
    """Process documents and generate 10 one-minute segments."""
    
    # Get OpenAI client from singleton
    client = OpenAIClient.get_client()
    
    # Combine all document contents
    combined_text = ""
    for file_path in file_paths:
        try:
            if file_path.suffix.lower() == '.pdf':
                text = await extract_text_from_pdf(file_path)
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except UnicodeDecodeError:
                    # Try alternate encoding if UTF-8 fails
                    with open(file_path, 'r', encoding='latin-1') as f:
                        text = f.read()
            
            combined_text += text + "\n\n"
            print(f"Successfully processed: {file_path}")
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            raise

    if not combined_text.strip():
        raise Exception("No content could be extracted from the uploaded documents")
    
    try:
        # Generate segments using OpenAI
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": """You are a true crime documentary writer. 
                Create exactly 10 one-minute segments that tell a compelling story.
                Each segment should be self-contained and dramatically paced."""},
                {"role": "user", "content": f"Create 10 one-minute segments from this story: {combined_text}"}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse segments from response
        segments = [s.strip() for s in response.choices[0].message.content.split("\n\n") if s.strip()]
        
        if not segments:
            raise Exception("No segments were generated")
            
        # Ensure exactly 10 segments
        if len(segments) < 10:
            # Pad with empty segments if needed
            segments.extend(["[Segment content to be generated]"] * (10 - len(segments)))
        return segments[:10]
        
    except Exception as e:
        print(f"Error in document processing: {str(e)}")
        raise Exception(f"Failed to process documents: {str(e)}") 