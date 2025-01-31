import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import streamlit as st
import atexit

@dataclass
class DocumentarySegment:
    """A single segment of the documentary with its associated data"""
    text: str
    prompt: str
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    feedback: Dict[str, Any] = None
    metrics: Dict[str, float] = None

class ExperimentTracker:
    def __init__(self, project_name: str = "Crime-Doc-Generator"):
        """Initialize the experiment tracker"""
        self.project_name = project_name
        self.segments: List[DocumentarySegment] = []
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.has_error = False
        self.wandb = None
        
        # Create local storage directory if it doesn't exist
        self.storage_dir = os.path.join("experiments", self.run_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize W&B synchronously
        self._init_wandb()
        
        # Register cleanup handler
        atexit.register(self._cleanup)
    
    def _init_wandb(self):
        """Initialize W&B connection synchronously"""
        try:
            import wandb
            if wandb.run is None:
                self.wandb = wandb.init(
                    project=self.project_name,
                    settings=wandb.Settings(start_method="thread")
                )
            else:
                self.wandb = wandb.run
        except Exception as e:
            st.warning(f"W&B initialization failed: {str(e)}. Continuing with local storage only.")
            self.wandb = None
    
    def _cleanup(self):
        """Cleanup resources on exit"""
        if self.wandb:
            try:
                self.wandb.finish()
            except:
                pass
    
    def start_segment(self, text: str, prompt: str) -> int:
        """Start tracking a new segment"""
        segment = DocumentarySegment(
            text=text,
            prompt=prompt
        )
        self.segments.append(segment)
        
        # Log locally
        self._save_local_state()
        
        # Log to W&B if available
        if self.wandb:
            self.wandb.log({
                "segment_text": text,
                "segment_prompt": prompt,
                "segment_number": len(self.segments) - 1
            })
        
        return len(self.segments) - 1
    
    def update_segment(self, 
                      segment_idx: int, 
                      image_path: Optional[str] = None,
                      audio_path: Optional[str] = None,
                      video_path: Optional[str] = None):
        """Update a segment with generated content"""
        segment = self.segments[segment_idx]
        
        if image_path:
            segment.image_path = image_path
            if self.wandb:
                try:
                    self.wandb.log({f"segment_{segment_idx}_image": wandb.Image(image_path)})
                except Exception:
                    pass
            
        if audio_path:
            segment.audio_path = audio_path
            if self.wandb:
                try:
                    self.wandb.log({f"segment_{segment_idx}_audio": wandb.Audio(audio_path)})
                except Exception:
                    pass
            
        if video_path:
            segment.video_path = video_path
            if self.wandb:
                self.wandb.log({f"segment_{segment_idx}_video": video_path})
        
        # Save state locally
        self._save_local_state()
    
    def log_error(self, error_message: str):
        """Log an error event"""
        self.has_error = True
        error_data = {
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log locally
        error_path = os.path.join(self.storage_dir, "errors.json")
        try:
            if os.path.exists(error_path):
                with open(error_path, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
            errors.append(error_data)
            with open(error_path, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            st.error(f"Failed to log error locally: {str(e)}")
        
        # Log to W&B if available
        if self.wandb:
            try:
                self.wandb.log({
                    "error": error_message,
                    "error_timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                st.error(f"Failed to log error to W&B: {str(e)}")

    def log_metrics(self, metrics: Dict[str, float]):
        """Log metrics for the entire run"""
        # Save locally
        metrics_path = os.path.join(self.storage_dir, "metrics.json")
        try:
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save metrics locally: {str(e)}")
        
        # Log to W&B if available
        if self.wandb:
            try:
                self.wandb.log(metrics)
            except Exception as e:
                st.error(f"Failed to log metrics to W&B: {str(e)}")
    
    def add_feedback(self, 
                    segment_idx: int, 
                    feedback: Dict[str, Any]) -> bool:
        """Add human feedback to a segment"""
        segment = self.segments[segment_idx]
        segment.feedback = feedback
        
        # Log locally
        self._save_local_state()
        
        # Log to W&B if available
        if self.wandb:
            self.wandb.log({
                f"segment_{segment_idx}_feedback": feedback
            })
        
        # Return True if regeneration is needed
        return bool(feedback.get("needs_regeneration", False))
    
    def _save_local_state(self):
        """Save current state to local storage"""
        state_path = os.path.join(self.storage_dir, "state.json")
        
        # Convert segments to dictionary format
        segments_data = []
        for segment in self.segments:
            segment_dict = {
                "text": segment.text,
                "prompt": segment.prompt,
                "image_path": segment.image_path,
                "audio_path": segment.audio_path,
                "video_path": segment.video_path,
                "feedback": segment.feedback,
                "metrics": segment.metrics
            }
            segments_data.append(segment_dict)
        
        # Save to file
        with open(state_path, 'w') as f:
            json.dump({
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat(),
                "segments": segments_data
            }, f, indent=2)
    
    def save_experiment(self):
        """Save the experiment data"""
        self._save_local_state()
        
        # Log final state to W&B if available
        if self.wandb:
            try:
                self.wandb.log({
                    "run_id": self.run_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_segments": len(self.segments),
                    "has_error": self.has_error
                })
            except Exception as e:
                st.warning(f"Failed to save final state to W&B: {str(e)}")
    
    def finish(self):
        """Finish the experiment and clean up"""
        self.save_experiment()
        self._cleanup()

# Initialize global tracker
tracker = ExperimentTracker() 