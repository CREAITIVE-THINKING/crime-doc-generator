import streamlit as st
import os
from dotenv import load_dotenv
from processors.document_processor import process_documents
from processors.image_generator import generate_images, generate_sd_prompts
from processors.audio_generator import generate_voiceovers
from processors.video_generator import create_video_segments
from processors.experiment_tracker import tracker
import asyncio
from pathlib import Path
import openai

load_dotenv()

st.set_page_config(page_title="True Crime Documentary Generator", layout="wide")

async def main():
    st.title("True Crime Documentary Generator")
    
    # Story title
    story_title = st.text_input("Story Title", "Untitled Documentary")
    
    # File upload section
    st.header("1. Upload Documents")
    uploaded_files = st.file_uploader("Upload case files (PDF, TXT)", 
                                    type=["pdf", "txt"], 
                                    accept_multiple_files=True)
    
    # Character reference image
    st.header("2. Upload Character Reference")
    character_image = st.file_uploader("Upload character reference image", 
                                     type=["png", "jpg", "jpeg"])
    
    # Voice selection
    st.header("3. Select Voice")
    voice_options = {
        "Rachel": "21m00Tcm4TlvDq8ikWAM",
        "Drew": "29vD33N1CtxCmqQRPOHJ",
        "Charlotte": "XB0fDUnXU5powFXDhCwa"
    }
    selected_voice = st.selectbox("Choose narrator voice", list(voice_options.keys()))
    
    if st.button("Generate Documentary Segments") and uploaded_files and character_image:
        with st.spinner("Processing..."):
            try:
                # Create temporary directory for processing
                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                
                # Save uploaded files
                file_paths = []
                for file in uploaded_files:
                    file_path = temp_dir / file.name
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    file_paths.append(file_path)
                
                # Save character image
                char_image_path = temp_dir / character_image.name
                with open(char_image_path, "wb") as f:
                    f.write(character_image.getbuffer())
                
                # Process documents
                st.text("Processing documents...")
                segments = await process_documents(file_paths)
                
                # Process each segment
                for i, segment in enumerate(segments):
                    st.subheader(f"Segment {i+1}")
                    
                    # Start tracking this segment
                    segment_idx = tracker.start_segment(
                        text=segment,
                        prompt=""  # We'll update this after generating the prompt
                    )
                    
                    # Generate and display content
                    prompt = await generate_sd_prompts(segment, openai.AsyncOpenAI())
                    
                    # Update tracker with the prompt
                    tracker.update_segment(segment_idx, prompt=prompt)
                    
                    # Generate content
                    image_paths = await generate_images([segment], str(char_image_path))
                    audio_paths = await generate_voiceovers([segment], voice_options[selected_voice])
                    video_paths = await create_video_segments(image_paths, audio_paths)
                    
                    # Update tracker with paths
                    tracker.update_segment(
                        segment_idx,
                        image_path=image_paths[0] if image_paths else None,
                        audio_path=audio_paths[0] if audio_paths else None,
                        video_path=video_paths[0] if video_paths else None
                    )
                    
                    # Display content
                    st.write("**Segment Text:**")
                    st.write(segment)
                    st.write("**Generated Prompt:**")
                    st.write(prompt)
                    
                    if image_paths:
                        st.image(image_paths[0])
                    if audio_paths:
                        st.audio(audio_paths[0])
                    
                    # Feedback collection
                    with st.expander("Provide Feedback"):
                        feedback = {}
                        feedback["text_rating"] = st.slider(
                            "Rate the story segment (1-5)", 
                            1, 5, 3, 
                            key=f"text_{i}"
                        )
                        feedback["prompt_rating"] = st.slider(
                            "Rate the image prompt (1-5)", 
                            1, 5, 3, 
                            key=f"prompt_{i}"
                        )
                        feedback["revised_prompt"] = st.text_area(
                            "Suggest prompt improvements", 
                            key=f"revision_{i}"
                        )
                        feedback["comments"] = st.text_area(
                            "Additional comments", 
                            key=f"comments_{i}"
                        )
                        
                        if st.button("Submit Feedback", key=f"submit_{i}"):
                            needs_regeneration = tracker.add_feedback(i, feedback)
                            if needs_regeneration:
                                st.warning("Regenerating content with revised prompt...")
                                # Regenerate content logic would go here
                
                # Save run when complete
                tracker.save_experiment()
                
                # Show download links
                st.success("Processing complete!")
                for i, video_path in enumerate(video_paths):
                    with open(video_path, "rb") as f:
                        st.download_button(
                            f"Download Segment {i+1}",
                            f,
                            file_name=f"segment_{i+1}.mp4",
                            mime="video/mp4"
                        )
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                tracker.log_error(error_message)
            finally:
                # Cleanup temp files
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    st.warning(f"Failed to clean up temporary files: {str(cleanup_error)}")
                
                # Always try to save the experiment
                try:
                    tracker.save_experiment()
                    tracker.finish()
                except Exception as save_error:
                    st.warning(f"Failed to save experiment data: {str(save_error)}")

if __name__ == "__main__":
    asyncio.run(main()) 