"""
TTS Gateway API - Main FastAPI Application

A unified gateway for routing TTS requests to multiple providers.
Supports: cartesia, gemini, gtts, elevenlabs, xiaomi, vnpost, minimax

Usage:
    uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gateway.schemas import (
    TTSRequest, TTSResponse, HealthStatus, ProviderInfo,
    VoiceConfig, AudioConfig, CloneRequest, TTSError
)
from gateway.router import ProviderRouter, DirectProviderAdapter
from gateway.config import GatewayConfig

# Configure logging
logging.basicConfig(
    level=getattr(logging, GatewayConfig.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TTSGateway")

# Configuration from GatewayConfig
OUTPUT_DIR = GatewayConfig.OUTPUT_DIR
UPLOAD_DIR = GatewayConfig.UPLOAD_DIR
CONFIG_FILE = GatewayConfig.PROVIDERS_CONFIG_FILE

# Ensure directories exist
GatewayConfig.ensure_directories()

# Global router instance
router: Optional[ProviderRouter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global router
    
    # Startup
    logger.info("🚀 TTS Gateway starting up...")
    
    logger.info(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    logger.info(f"📁 Upload directory: {UPLOAD_DIR.absolute()}")
    
    # Initialize router
    router = ProviderRouter(output_dir=OUTPUT_DIR)
    
    # Auto-register commonly used providers
    auto_register_providers = [
        "cartesia",
        "gemini", 
        "gtts",
        "elevenlabs",
        "xiaomi",
        "vnpost",
        "minimax_selenium",
    ]
    
    for provider_name in auto_register_providers:
        try:
            success = router.register_provider(provider_name)
            if success:
                logger.info(f"✅ Auto-registered: {provider_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not register {provider_name}: {e}")
    
    # Try to load from config file if exists
    if CONFIG_FILE.exists():
        try:
            results = router.register_providers_from_config(CONFIG_FILE)
            success_count = sum(1 for v in results.values() if v)
            logger.info(f"✅ Loaded {success_count}/{len(results)} providers from config")
        except Exception as e:
            logger.warning(f"⚠️ Could not load config file: {e}")
    
    registered = router.list_providers()
    logger.info(f"🎯 Ready with {len(registered)} providers: {registered}")
    
    yield
    
    # Shutdown
    logger.info("🛑 TTS Gateway shutting down...")


# Create FastAPI application
app = FastAPI(
    title="TTS Gateway API",
    description="""
    Unified gateway for Text-to-Speech synthesis across multiple providers.
    
    ## Supported Providers
    
    - **cartesia** - Cartesia Sonic TTS
    - **gemini** - Google Gemini TTS
    - **gtts** - Google Text-to-Speech (gTTS)
    - **elevenlabs** - ElevenLabs TTS
    - **xiaomi** - Xiaomi OmniVoice (voice cloning)
    - **vnpost** - VNPost TTS
    - **minimax_selenium** - MiniMax TTS (via Selenium)
    
    ## Usage
    
    Send a POST request to `/tts` with your synthesis parameters.
    The gateway will route to the appropriate provider and return the audio file path.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=GatewayConfig.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TTS Gateway API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "providers": "/providers",
        "synthesize": "POST /tts",
        "clone": "POST /clone (multipart form for voice cloning)"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns overall gateway status and provider health information.
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    provider_health = await router.health_check()
    
    healthy_count = sum(1 for h in provider_health.values() if h.status == "healthy")
    total_count = len(provider_health)
    
    return {
        "status": "healthy" if healthy_count > 0 else "degraded",
        "timestamp": datetime.now().isoformat(),
        "providers": {
            "total": total_count,
            "healthy": healthy_count,
            "details": {name: h.model_dump() for name, h in provider_health.items()}
        }
    }


@app.get("/providers")
async def list_providers():
    """
    List all registered TTS providers with their information.
    
    Returns detailed information about each available provider including
    supported voices, models, and configuration.
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    providers_info = router.get_provider_info()
    available_types = router.list_available_provider_types()
    registered = router.list_providers()
    
    return {
        "registered": registered,
        "available_types": available_types,
        "providers_info": providers_info
    }


@app.get("/providers/{provider_name}")
async def get_provider_info(provider_name: str):
    """
    Get detailed information about a specific provider.
    
    Args:
        provider_name: Name of the provider (e.g., 'cartesia', 'gemini')
        
    Returns:
        Provider metadata including supported voices and configuration
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    info = router.get_provider_info(provider_name)
    
    if provider_name.lower() not in router.list_providers():
        available = router.list_available_provider_types()
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not found. Available: {available}"
        )
    
    return info


@app.post("/tts", response_model=TTSResponse)
async def synthesize(request: TTSRequest):
    """
    Synthesize text to speech.
    
    This is the main endpoint for TTS synthesis. The gateway will route the request
to the appropriate provider based on the `provider` field.
    
    ## Request Body
    
    - **provider** (required): TTS provider name
    - **text** (required): Text to synthesize
    - **model**: Model identifier (provider-specific)
    - **voice_config**: Voice settings (voice_id, volume, speed, emotion, language)
    - **audio_config**: Audio settings (container, encoding, sample_rate, bit_rate, channel)
    
    ## Example Request
    
    ```json
    {
        "provider": "cartesia",
        "text": "Xin chào, đây là giọng nói được tạo ra bởi Cartesia.",
        "model": "sonic-3",
        "voice_config": {
            "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
            "language": "vi",
            "volume": 1.0,
            "speed": 1.0,
            "emotion": "neutral"
        },
        "audio_config": {
            "container": "mp3",
            "encoding": "pcm_f32le",
            "sample_rate": 44100
        }
    }
    ```
    
    ## Response
    
    On success:
    - `success`: true
    - `audio_url`: Path to generated audio file
    - `effective_voice_config`: Actual voice settings used
    - `effective_audio_config`: Actual audio settings used
    
    On failure:
    - `success`: false
    - `error.message`: Error description
    - `error.detail`: Additional error details
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    logger.info(f"📝 TTS request: provider={request.provider}, text='{request.text[:50]}...'")
    
    try:
        response = await router.route_request(request)
        
        if not response.success:
            logger.warning(f"❌ Synthesis failed: {response.error}")
            # Return 200 with error details (not 500, since this is provider error)
            return response
        
        logger.info(f"✅ Synthesis successful: {response.audio_url}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Gateway error: {e}")
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")


@app.post("/clone", response_model=TTSResponse)
async def clone_voice(
    provider: str = Form(..., description="TTS provider name (e.g., 'xiaomi', 'minimax_selenium')"),
    text: str = Form(..., description="Text to synthesize using cloned voice"),
    reference_audio: UploadFile = File(..., description="Reference audio file to clone voice from"),
    model: Optional[str] = Form(None, description="Model identifier (provider-specific)"),
    reference_text: Optional[str] = Form(None, description="Transcript of reference audio (optional)"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'vi', 'en')"),
    enhance_speech: Optional[bool] = Form(None, description="Enhance reference audio before cloning"),
    volume: Optional[float] = Form(None, ge=0.0, le=1.0, description="Volume multiplier (0.0-1.0)"),
    speed: Optional[float] = Form(None, ge=0.5, le=2.0, description="Speech rate multiplier (0.5-2.0)"),
    pitch: Optional[float] = Form(None, description="Pitch adjustment in semitones"),
    emotion: Optional[str] = Form(None, description="Emotion or style tag"),
    container: Optional[str] = Form(None, description="Audio container format (raw/wav/mp3)"),
    sample_rate: Optional[int] = Form(None, description="Audio sample rate"),
):
    """
    Voice cloning endpoint using multipart form upload.
    
    This endpoint is specifically for providers that support voice cloning (e.g., Xiaomi, MiniMax).
    Upload a reference audio file and the provider will clone the voice to synthesize the text.
    
    ## Form Fields
    
    - **provider** (required): Provider name ('xiaomi', 'minimax_selenium')
    - **text** (required): Text to synthesize
    - **reference_audio** (required): Audio file to clone voice from (wav, mp3, etc.)
    - **reference_text**: Transcript of reference audio (optional, improves quality)
    - **language**: Language code (e.g., 'vi')
    - **enhance_speech**: Whether to enhance the reference audio (default: true)
    - **volume/speed/pitch/emotion**: Voice tuning options
    - **container**: Output audio format ('wav', 'mp3')
    - **sample_rate**: Output sample rate (e.g., 24000, 44100)
    
    ## Example (cURL)
    
    ```bash
    curl -X POST http://localhost:8000/clone \
        -F "provider=xiaomi" \
        -F "text=Xin chào, đây là giọng nói được clone." \
        -F "reference_audio=@/path/to/reference.wav" \
        -F "reference_text=Transcript của audio mẫu" \
        -F "language=vi" \
        -F "enhance_speech=true"
    ```
    
    ## Example (Python requests)
    
    ```python
    import requests
    
    with open("reference.wav", "rb") as f:
        files = {"reference_audio": f}
        data = {
            "provider": "xiaomi",
            "text": "Xin chào, đây là giọng nói được clone.",
            "reference_text": "Transcript của audio mẫu",
            "language": "vi"
        }
        response = requests.post("http://localhost:8000/clone", files=files, data=data)
        print(response.json())
    ```
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    logger.info(f"🎭 Clone request: provider={provider}, text='{text[:50]}...'")
    
    try:
        # Save uploaded reference audio to temp file
        import tempfile
        import shutil
        
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        ref_ext = Path(reference_audio.filename).suffix if reference_audio.filename else ".wav"
        ref_filename = f"ref_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ref_ext}"
        ref_path = UPLOAD_DIR / ref_filename
        
        with open(ref_path, "wb") as f:
            shutil.copyfileobj(reference_audio.file, f)
        
        logger.info(f"📁 Reference audio saved: {ref_path}")
        
        # Build TTSRequest with ReplicatedVoiceConfig
        from gateway.schemas import TTSRequest, VoiceConfig, AudioConfig
        
        voice_cfg = VoiceConfig(
            voice_id=None,
            reference_audio=str(ref_path),
            reference_text=reference_text,
            enhance_speech=enhance_speech if enhance_speech is not None else True,
            language=language,
            volume=volume,
            speed=speed,
            pitch=pitch,
            emotion=emotion,
        )
        
        audio_cfg = AudioConfig(
            container=container or "wav",
            sample_rate=sample_rate,
        ) if container or sample_rate else None
        
        request = TTSRequest(
            provider=provider,
            text=text,
            model=model,
            voice_config=voice_cfg,
            audio_config=audio_cfg,
        )
        
        # Route to provider using dedicated clone method
        response = await router.route_clone_request(request)
        
        # Clean up reference audio on success (optional - keep for debugging)
        # if response.success:
        #     ref_path.unlink(missing_ok=True)
        
        if not response.success:
            logger.warning(f"❌ Clone failed: {response.error}")
        else:
            logger.info(f"✅ Clone successful: {response.audio_url}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Clone error: {e}")
        raise HTTPException(status_code=500, detail=f"Clone error: {str(e)}")


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Retrieve a generated audio file.
    
    Args:
        filename: Name of the audio file (including extension)
        
    Returns:
        Audio file with appropriate content type
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio file not found: {filename}")
    
    # Determine content type based on extension
    ext = filename.lower().split('.')[-1]
    content_type_map = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'raw': 'audio/raw',
    }
    content_type = content_type_map.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename
    )


@app.post("/providers/{provider_name}/register")
async def register_provider(provider_name: str, config: Optional[Dict[str, Any]] = None):
    """
    Dynamically register a new provider instance.
    
    Args:
        provider_name: Name of the provider to register
        config: Optional configuration dictionary
        
    Returns:
        Registration status
    """
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")
    
    available = router.list_available_provider_types()
    
    if provider_name.lower() not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider type '{provider_name}'. Available: {available}"
        )
    
    try:
        success = router.register_provider(provider_name, config or {})
        
        if success:
            return {
                "success": True,
                "message": f"Provider '{provider_name}' registered successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register provider '{provider_name}'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration error: {str(e)}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "message": "Invalid request",
                "detail": str(exc)
            }
        }
    )


@app.exception_handler(Exception)
async def general_error_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "detail": str(exc)
            }
        }
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting TTS Gateway on {GatewayConfig.HOST}:{GatewayConfig.PORT}")
    uvicorn.run(
        "gateway.main:app",
        host=GatewayConfig.HOST,
        port=GatewayConfig.PORT,
        reload=GatewayConfig.RELOAD
    )
