"""
TUBECRAFT Generator Service
Main FastAPI application for content generation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import structlog
from datetime import datetime
from typing import Dict, Any
import os

from .models import EpisodeRequest, EpisodeResponse, GenerationStatus
from .services.ollama_service import OllamaService
from .services.tts_service import TTSService
from .services.video_service import VideoService
from .services.database_service import DatabaseService
from .core.config import settings
from .core.logging import setup_logging

# Setup structured logging
logger = structlog.get_logger()

# Global service instances
ollama_service = None
tts_service = None
video_service = None
db_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ollama_service, tts_service, video_service, db_service
    
    logger.info("Starting TUBECRAFT Generator Service")
    
    # Initialize services
    try:
        ollama_service = OllamaService(settings.ollama_host)
        tts_service = TTSService()
        video_service = VideoService()
        db_service = DatabaseService(settings.database_url)
        
        await db_service.connect()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down TUBECRAFT Generator Service")
    if db_service:
        await db_service.disconnect()


# Create FastAPI app
app = FastAPI(
    title="TUBECRAFT Generator",
    description="AI-powered content generation service for YouTube and Podcast",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tubecraft-generator",
        "version": "1.0.0"
    }


@app.get("/status")
async def service_status() -> Dict[str, Any]:
    """Detailed service status"""
    status = {
        "service": "tubecraft-generator",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Ollama
    try:
        ollama_status = await ollama_service.health_check()
        status["services"]["ollama"] = {"status": "healthy", "details": ollama_status}
    except Exception as e:
        status["services"]["ollama"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Database
    try:
        db_status = await db_service.health_check()
        status["services"]["database"] = {"status": "healthy", "details": db_status}
    except Exception as e:
        status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Check TTS
    try:
        tts_status = tts_service.health_check()
        status["services"]["tts"] = {"status": "healthy", "details": tts_status}
    except Exception as e:
        status["services"]["tts"] = {"status": "unhealthy", "error": str(e)}
    
    return status


@app.post("/episodes", response_model=EpisodeResponse)
async def create_episode(
    request: EpisodeRequest, 
    background_tasks: BackgroundTasks
) -> EpisodeResponse:
    """Create a new episode and start generation process"""
    
    logger.info("Creating new episode", title=request.title)
    
    try:
        # Create episode in database
        episode = await db_service.create_episode(
            title=request.title,
            description=request.description,
            content_style=request.content_style,
            target_duration_minutes=request.duration_minutes
        )
        
        # Start background generation
        background_tasks.add_task(
            generate_episode_content,
            episode.id,
            request
        )
        
        logger.info("Episode created successfully", episode_id=str(episode.id))
        
        return EpisodeResponse(
            id=episode.id,
            title=episode.title,
            status=GenerationStatus.QUEUED,
            created_at=episode.created_at
        )
        
    except Exception as e:
        logger.error("Failed to create episode", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(episode_id: str) -> EpisodeResponse:
    """Get episode status and details"""
    
    try:
        episode = await db_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        return EpisodeResponse(
            id=episode.id,
            title=episode.title,
            status=GenerationStatus(episode.status),
            created_at=episode.created_at,
            completed_at=episode.generation_completed_at,
            audio_path=episode.audio_path,
            video_path=episode.video_path,
            duration_seconds=episode.duration_seconds,
            error_message=episode.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get episode", episode_id=episode_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def generate_episode_content(episode_id: str, request: EpisodeRequest):
    """Background task to generate episode content"""
    
    logger.info("Starting episode generation", episode_id=episode_id)
    
    try:
        # Update status to generating
        await db_service.update_episode_status(
            episode_id, 
            GenerationStatus.GENERATING_SCRIPT
        )
        
        # Generate script using Ollama
        logger.info("Generating script", episode_id=episode_id)
        script = await ollama_service.generate_script(
            title=request.title,
            description=request.description or "",
            duration_minutes=request.duration_minutes,
            style=request.content_style
        )
        
        # Update status and save script
        await db_service.update_episode_status(
            episode_id, 
            GenerationStatus.GENERATING_AUDIO
        )
        await db_service.update_episode_script(episode_id, script)
        
        # Generate audio using TTS
        logger.info("Generating audio", episode_id=episode_id)
        audio_path = await tts_service.generate_audio(
            script=script,
            episode_id=episode_id,
            voice_speed=request.voice_speed
        )
        
        # Update status
        await db_service.update_episode_status(
            episode_id, 
            GenerationStatus.GENERATING_VIDEO
        )
        
        # Generate video
        logger.info("Generating video", episode_id=episode_id)
        video_path = await video_service.create_video(
            audio_path=audio_path,
            script=script,
            title=request.title,
            episode_id=episode_id
        )
        
        # Update final status
        await db_service.complete_episode(
            episode_id=episode_id,
            audio_path=audio_path,
            video_path=video_path,
            duration_seconds=script.get("total_duration", 0)
        )
        
        logger.info("Episode generation completed", episode_id=episode_id)
        
    except Exception as e:
        logger.error("Episode generation failed", episode_id=episode_id, error=str(e))
        await db_service.fail_episode(episode_id, str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENV") == "development" else False
    )