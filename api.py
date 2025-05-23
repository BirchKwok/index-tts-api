import os
import torch
import logging
import argparse
import platform
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path

from indextts.infer import IndexTTS

# Configure logging
logging.basicConfig(level=logging.INFO)

root_dir = Path(__file__).resolve().parent
model_dir = root_dir / "checkpoints"
output_audio_dir = root_dir / "outputs/api"

app_config = {
    "model_dir": model_dir.absolute(),
    "device_id": 0,
    "output_dir": output_audio_dir.absolute()
}

def initialize_model(model_dir=model_dir, device_id=0):
    """Load the model once at the beginning."""
    model_dir = Path(model_dir).absolute()

    logging.info(f"Loading model from: {model_dir}")

    # Determine appropriate device based on platform and availability
    if platform.system() == "Darwin":
        # macOS with MPS support (Apple Silicon)
        device = torch.device("cpu")
        # device = torch.device(f"mps:{device_id}")
        logging.info(f"Using device: {device}")
    elif torch.cuda.is_available():
        # System with CUDA support
        device = torch.device(f"cuda:{device_id}")
        logging.info(f"Using CUDA device: {device}")
    else:
        # Fall back to CPU
        device = torch.device("cpu")
        logging.info("GPU acceleration not available, using CPU")

    try:
        print(f"Loading model from {model_dir} on device {device}")
        cfg_path = model_dir / "config.yaml"
        model = IndexTTS(
            cfg_path=str(cfg_path),
            model_dir=str(model_dir),
            is_fp16=True if device.type == "cuda" else False,
            device=str(device)
        )
        logging.info("Model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        raise RuntimeError(f"Could not load IndexTTS model from {model_dir}")


def run_tts(
    text: str,
    model: IndexTTS,
    prompt_text: Optional[str] = None,
    prompt_speech_path: Optional[str] = None,
    gender: Optional[str] = None,
    pitch: Optional[str] = None,
    speed: Optional[str] = None,
    save_dir: str = "outputs/api",
) -> str:
    """Perform TTS inference and save the generated audio. Returns the path to the audio file."""
    logging.info(f"Saving audio to: {save_dir}")

    if prompt_text is not None:
        prompt_text = None if len(prompt_text) <= 1 else prompt_text

    os.makedirs(save_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S_%f")
    save_path = os.path.join(save_dir, f"tts_output_{timestamp}.wav")

    logging.info("Starting TTS inference...")

    try:
        # IndexTTS只需要音频提示文件，其他参数暂时忽略
        if prompt_speech_path is None:
            # 如果没有提供参考音频，创建一个默认的参考音频路径
            default_prompt = os.path.join("tests", "sample_prompt.wav")
            if os.path.exists(default_prompt):
                prompt_speech_path = default_prompt
            else:
                raise ValueError("No prompt audio provided and no default prompt audio found")
        
        # 使用IndexTTS进行推理
        output_path = model.infer(
            audio_prompt=prompt_speech_path,
            text=text,
            output_path=save_path,
            verbose=True
        )
        logging.info(f"Audio saved at: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Error during TTS inference: {e}")
        # Consider removing the partially created file if an error occurs
        if os.path.exists(save_path):
            os.remove(save_path)
        raise RuntimeError(f"TTS inference failed: {e}")


def parse_arguments():
    """
    Parse command-line arguments such as model directory and device ID.
    """
    parser = argparse.ArgumentParser(description="IndexTTS API server.")
    parser.add_argument(
        "--model_dir",
        type=str,
        default="checkpoints",
        help="Path to the model directory."
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="ID of the GPU/MPS device to use (e.g., 0 for cuda:0 or mps:0)."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host for the API server."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the API server."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs/api",
        help="Directory to save generated audio files."
    )
    return parser.parse_args()


# Global variable to hold the model and output directory
model_tts: Optional[IndexTTS] = None

# Global dictionary for idempotency tracking (Not production-ready)
idempotency_cache = {}

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Load the model and set up configurations when the server starts."""
    global model_tts, output_audio_dir
    # Use configuration from app_config dictionary
    logging.info(f"Lifespan startup: Loading model from {app_config['model_dir']}")
    model_tts = initialize_model(model_dir=app_config['model_dir'], device_id=app_config['device_id'])
    output_audio_dir = app_config['output_dir']
    # Ensure output directory exists
    os.makedirs(output_audio_dir, exist_ok=True)
    logging.info(f"Lifespan startup complete. Model loaded. Output directory: {output_audio_dir}")
    yield  # Application runs here
    # Clean up resources if needed on shutdown (optional)
    logging.info("Lifespan shutdown.")
    model_tts = None # Release model resources if applicable

# Original app definition needs to happen early for decorators
app = FastAPI(lifespan=lifespan)

class TTSCreateRequest(BaseModel):
    text: str
    gender: str  # 'male' or 'female' (暂时忽略，IndexTTS通过参考音频控制音色)
    pitch: int   # 1-5 (暂时忽略)
    speed: int   # 1-5 (暂时忽略)

@app.get("/hello")
async def hello():
    """
    Returns a greeting message from the API.
    """
    return {"message": "Hello! I am the IndexTTS API service. Nice to meet you!"}

@app.post("/tts/create", response_class=FileResponse)
async def api_create_voice(
    text: str = Form(...),
    gender: str = Form(...),
    pitch: int = Form(...),
    speed: int = Form(...),
    idempotency_key: Optional[str] = Form(None)  # Add idempotency key
):
    """
    Create a synthetic voice with adjustable parameters.
    Supports idempotency via idempotency_key.
    Returns the generated WAV audio file.
    
    Note: IndexTTS使用参考音频控制音色，gender/pitch/speed参数暂时忽略
    """
    global idempotency_cache # Ensure we can modify the global cache

    # Check idempotency cache first
    if idempotency_key and idempotency_key in idempotency_cache:
        cached_result_path = idempotency_cache[idempotency_key]
        if os.path.exists(cached_result_path):
            logging.info(f"Returning cached result for idempotency key: {idempotency_key}")
            return FileResponse(path=cached_result_path, media_type='audio/wav', filename=os.path.basename(cached_result_path))
        else:
            # Cached file might have been deleted, remove from cache and proceed
            logging.warning(f"Cached file not found for key {idempotency_key}. Re-processing.")
            del idempotency_cache[idempotency_key]


    if not model_tts:
        raise HTTPException(status_code=503, detail="Model not loaded yet. Please try again shortly.")
    if gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid gender. Choose 'male' or 'female'.")
    if not (1 <= pitch <= 5):
        raise HTTPException(status_code=400, detail="Invalid pitch. Choose an integer between 1 and 5.")
    if not (1 <= speed <= 5):
        raise HTTPException(status_code=400, detail="Invalid speed. Choose an integer between 1 and 5.")

    try:
        # IndexTTS目前忽略这些参数，主要通过参考音频控制
        audio_output_path = run_tts(
            text=text,
            model=model_tts,
            gender=gender,
            pitch=str(pitch),
            speed=str(speed),
            save_dir=output_audio_dir
        )

        # Store result in idempotency cache if key was provided
        if idempotency_key:
            idempotency_cache[idempotency_key] = audio_output_path
            logging.info(f"Stored result for idempotency key: {idempotency_key}")

        return FileResponse(path=audio_output_path, media_type='audio/wav', filename=os.path.basename(audio_output_path))
    except RuntimeError as e:
        logging.error(f"TTS creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/clone", response_class=FileResponse)
async def api_clone_voice(
    text: str = Form(...),
    prompt_audio: UploadFile = File(...),
    prompt_text: Optional[str] = Form(None),      # Text of the prompt audio (optional)
    idempotency_key: Optional[str] = Form(None),
    # Optional parameters for customization
    gender: Optional[str] = Form(None),      # 'male' or 'female' (暂时忽略)
    pitch: Optional[int] = Form(None),       # 1-5 (暂时忽略)
    speed: Optional[int] = Form(None)        # 1-5 (暂时忽略)
):
    """
    Clone voice using text and a prompt audio file. Optionally customize the output voice.

    Args:
        text (str): The text to synthesize.
        prompt_audio (UploadFile): The reference audio file for voice cloning.
        prompt_text (Optional[str], optional): Text content of the prompt audio. Defaults to None.
        idempotency_key (Optional[str], optional): A unique key to ensure idempotency. Defaults to None.
        gender (Optional[str], optional): Gender parameter (暂时忽略). Defaults to None.
        pitch (Optional[int], optional): Pitch parameter (暂时忽略). Defaults to None.
        speed (Optional[int], optional): Speed parameter (暂时忽略). Defaults to None.

    Returns:
        FileResponse: The generated WAV audio file.

    Raises:
        HTTPException: 400 if validation fails for gender, pitch, or speed.
        HTTPException: 500 if TTS generation fails.
        HTTPException: 503 if the model is not loaded.
    """
    global idempotency_cache # Ensure we can modify the global cache

    # Check idempotency cache first
    if idempotency_key and idempotency_key in idempotency_cache:
        cached_result_path = idempotency_cache[idempotency_key]
        if os.path.exists(cached_result_path):
            logging.info(f"Returning cached result for idempotency key: {idempotency_key}")
            # Note: We don't need the uploaded prompt_audio if returning cached result
            return FileResponse(path=cached_result_path, media_type='audio/wav', filename=os.path.basename(cached_result_path))
        else:
            # Cached file might have been deleted, remove from cache and proceed
            logging.warning(f"Cached file not found for key {idempotency_key}. Re-processing.")
            del idempotency_cache[idempotency_key]

    if not model_tts:
        raise HTTPException(status_code=503, detail="Model not loaded yet. Please try again shortly.")

    # Validate optional parameters if provided
    if gender is not None and gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid gender. Choose 'male' or 'female'.")
    if pitch is not None and not (1 <= pitch <= 5):
        raise HTTPException(status_code=400, detail="Invalid pitch. Choose an integer between 1 and 5.")
    if speed is not None and not (1 <= speed <= 5):
        raise HTTPException(status_code=400, detail="Invalid speed. Choose an integer between 1 and 5.")

    # Save the uploaded prompt audio to a temporary file
    temp_prompt_path = os.path.join(output_audio_dir, f"prompt_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}_{prompt_audio.filename}")
    try:
        with open(temp_prompt_path, "wb") as buffer:
            buffer.write(await prompt_audio.read())
        logging.info(f"Prompt audio saved to {temp_prompt_path}")

        audio_output_path = run_tts(
            text=text,
            model=model_tts,
            prompt_text=prompt_text,
            prompt_speech_path=temp_prompt_path,
            # Pass customization parameters (目前暂时忽略)
            gender=gender,
            pitch=str(pitch) if pitch is not None else None,
            speed=str(speed) if speed is not None else None,
            save_dir=output_audio_dir
        )

        # Store result in idempotency cache if key was provided
        if idempotency_key:
            idempotency_cache[idempotency_key] = audio_output_path
            logging.info(f"Stored result for idempotency key: {idempotency_key}")

        return FileResponse(path=audio_output_path, media_type='audio/wav', filename=os.path.basename(audio_output_path))
    except RuntimeError as e:
        logging.error(f"TTS cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary prompt file
        if os.path.exists(temp_prompt_path):
            try:
                os.remove(temp_prompt_path)
                logging.info(f"Cleaned up temporary prompt audio: {temp_prompt_path}")
            except OSError as e:
                logging.error(f"Error deleting temporary prompt audio {temp_prompt_path}: {e}")


if __name__ == "__main__":
    args = parse_arguments()

    # Update the global config dictionary with parsed arguments BEFORE running uvicorn
    # Ensure paths from arguments are resolved correctly relative to root_dir

    # Resolve model_dir from arguments
    parsed_model_dir_arg = Path(args.model_dir)
    if parsed_model_dir_arg.is_absolute():
        app_config["model_dir"] = parsed_model_dir_arg.resolve()
    else:
        # If args.model_dir is relative, assume it's relative to the project root_dir
        app_config["model_dir"] = (root_dir / parsed_model_dir_arg).resolve()

    # Resolve output_dir from arguments
    parsed_output_dir_arg = Path(args.output_dir)
    if parsed_output_dir_arg.is_absolute():
        app_config["output_dir"] = parsed_output_dir_arg.resolve()
    else:
        # If args.output_dir is relative, assume it's relative to the project root_dir
        app_config["output_dir"] = (root_dir / parsed_output_dir_arg).resolve()

    app_config["device_id"] = args.device

    # Note: The model is loaded via the lifespan manager when uvicorn starts the app.
    # This avoids loading the model twice if __name__ == "__main__" is run directly by some tools.

    uvicorn.run(app, host=args.host, port=args.port) 