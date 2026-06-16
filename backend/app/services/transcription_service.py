import os
import gc
import logging
import subprocess
from typing import Dict, List, Any, Tuple

# Set up logging format
logger = logging.getLogger(__name__)

class LectureTranscriptionService:
    """
    A dedicated service to manage speech-to-text transcription for long lecture files.
    Optimized for low-memory environments using chunked processing, dynamic batching,
    and automatic audio extraction from video files via FFmpeg.
    """

    def __init__(self, model_id: str = "openai/whisper-small", use_gpu: bool = True):
        self.model_id = model_id
        self.use_gpu = use_gpu
        self.pipeline = None
        self.device = "cpu"
        self.torch_dtype = None

    def _initialize_pipeline(self):
        """
        Lazily loads the Hugging Face transformers speech recognition pipeline.
        Determines hardware availability (CUDA vs CPU) and configures dtype.
        """
        if self.pipeline is not None:
            return

        try:
            import torch
            from transformers import pipeline

            # Check for GPU capability and configure device and datatype
            if self.use_gpu and torch.cuda.is_available():
                self.device = "cuda:0"
                # Float16 uses half the memory compared to float32 on GPUs
                self.torch_dtype = torch.float16
                logger.info("GPU detected. Using CUDA with Float16 precision for Whisper.")
            else:
                self.device = "cpu"
                self.torch_dtype = torch.float32
                logger.info("Running Whisper inference on CPU with Float32 precision.")

            logger.info(f"Loading Whisper pipeline for model: {self.model_id}...")
            
            # Load the automatic speech recognition (ASR) pipeline
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.model_id,
                device=self.device,
                torch_dtype=self.torch_dtype,
                chunk_length_s=30,  # Whisper native frame buffer size
                trust_remote_code=True
            )
            logger.info("Whisper pipeline loaded successfully.")

        except ImportError as e:
            logger.error("Hugging Face transformers or PyTorch is not installed.")
            raise e
        except Exception as e:
            logger.error(f"Error initializing local Whisper pipeline: {e}")
            raise e

    def extract_audio_with_ffmpeg(self, video_path: str, output_audio_path: str) -> bool:
        """
        Invokes FFmpeg command-line subprocess to extract audio from video.
        Outputs a mono 16kHz WAV file, which is the native input shape for Whisper.
        """
        try:
            logger.info(f"FFmpeg: Extracting audio from {video_path} to {output_audio_path}")
            
            # CLI args:
            # -y: overwrite output
            # -i: input file path
            # -vn: skip video streams
            # -ac 1: convert to 1 mono channel
            # -ar 16000: resample rate to 16kHz
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                output_audio_path
            ]
            
            # Run the command silently
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error output: {result.stderr}")
                return False
                
            return True
        except FileNotFoundError:
            logger.error("FFmpeg binary not found on the system path. Please ensure FFmpeg is installed.")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error during FFmpeg execution: {e}")
            return False

    def _clean_memory(self):
        """
        Utility function to clear cached tensor memory on GPU/CPU to prevent Out of Memory errors.
        Called post-transcription.
        """
        try:
            import torch
            # Run Python Garbage Collector
            gc.collect()
            # Clear CUDA cache if GPU is enabled
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("CUDA memory cache cleared.")
        except Exception as e:
            logger.debug(f"Memory cleanup warning: {e}")

    def transcribe_lecture(
        self, 
        file_path: str, 
        batch_size: int = 4
    ) -> Dict[str, Any]:
        """
        Performs speech-to-text translation on the media file.
        Automatically processes video files by extracting their audio stream.
        
        Args:
            file_path: Absolute path to the source audio/video file.
            batch_size: Chunk batch size passed to HF pipeline. Low values lower RAM spikes.
            
        Returns:
            A dictionary containing:
              - 'full_transcript' (str)
              - 'timestamps' (list of dicts with 'start', 'end', and 'text')
              - 'detected_language' (str)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Ensure the pipeline is initialized
        self._initialize_pipeline()

        ext = os.path.splitext(file_path)[1].lower()
        working_audio_file = file_path
        temp_audio_created = False

        # If the input is a video file, extract audio using FFmpeg first
        if ext in [".mp4", ".mpeg", ".webm", ".avi", ".mov"]:
            working_audio_file = f"{os.path.splitext(file_path)[0]}_extracted.wav"
            success = self.extract_audio_with_ffmpeg(file_path, working_audio_file)
            if not success or not os.path.exists(working_audio_file):
                raise RuntimeError("Failed to extract audio from video file using FFmpeg.")
            temp_audio_created = True

        try:
            logger.info(f"Starting ASR process for: {working_audio_file}")
            
            # Configure pipeline arguments
            # batch_size=4 is a safe compromise between GPU VRAM limits and speed.
            # return_timestamps=True returns start/end offsets for each chunk.
            inference_args = {
                "batch_size": batch_size,
                "return_timestamps": True
            }

            # Run pipeline inference
            result = self.pipeline(working_audio_file, **inference_args)

            # Process segment outputs
            timestamps = []
            full_transcript_text = result.get("text", "").strip()
            
            # Hugging Face returns individual chunk details in "chunks"
            chunks = result.get("chunks", [])
            for chunk in chunks:
                time_range = chunk.get("timestamp", (0.0, 0.0))
                start = float(time_range[0]) if time_range[0] is not None else 0.0
                end = float(time_range[1]) if time_range[1] is not None else start + 3.0
                
                timestamps.append({
                    "start": start,
                    "end": end,
                    "text": chunk.get("text", "").strip()
                })

            # Detect language: pipeline attempts to look at the first few seconds
            # We can extract the language from model config outputs, or default to standard format
            detected_lang = "en"  # Default fallback
            
            # Try to grab language from transcription model metadata if present
            if hasattr(self.pipeline, "model") and hasattr(self.pipeline.model, "config"):
                # Whisper models store generation configs representing detected features
                gen_config = getattr(self.pipeline.model, "generation_config", None)
                if gen_config and hasattr(gen_config, "language"):
                    detected_lang = getattr(gen_config, "language", "en")

            logger.info("Inference completed successfully.")

            return {
                "full_transcript": full_transcript_text,
                "timestamps": timestamps,
                "detected_language": detected_lang
            }

        finally:
            # Clean up temporary extracted audio file if one was created
            if temp_audio_created and os.path.exists(working_audio_file):
                try:
                    os.remove(working_audio_file)
                    logger.debug("Cleaned up temporary audio extraction file.")
                except Exception as e:
                    logger.warning(f"Could not remove temp audio file {working_audio_file}: {e}")

            # Clear pipeline tensors from VRAM/RAM
            self._clean_memory()
