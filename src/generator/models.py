"""
TUBECRAFT Data Models
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class ContentStyle(str, Enum):
    """Content style enumeration"""
    EDUCATIONAL = "educational"
    NEWS = "news"
    ENTERTAINMENT = "entertainment" 
    PODCAST = "podcast"
    TUTORIAL = "tutorial"
    INTERVIEW = "interview"


class GenerationStatus(str, Enum):
    """Episode generation status"""
    DRAFT = "draft"
    QUEUED = "queued"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EpisodeRequest(BaseModel):
    """Request model for creating a new episode"""
    title: str = Field(..., min_length=1, max_length=500, description="Episode title")
    description: Optional[str] = Field(None, max_length=2000, description="Episode description")
    duration_minutes: int = Field(15, ge=5, le=60, description="Target duration in minutes")
    content_style: ContentStyle = Field(ContentStyle.EDUCATIONAL, description="Content style")
    voice_speed: float = Field(1.0, ge=0.5, le=2.0, description="TTS voice speed multiplier")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class EpisodeResponse(BaseModel):
    """Response model for episode data"""
    id: uuid.UUID
    title: str
    status: GenerationStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_mb: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ScriptSection(BaseModel):
    """A section of the generated script"""
    id: str
    type: str = Field(..., description="Section type (intro, main, conclusion, etc.)")
    content: str = Field(..., description="Section text content")
    duration_seconds: int = Field(..., ge=1, description="Expected duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Script(BaseModel):
    """Complete episode script"""
    title: str
    total_duration_seconds: int
    sections: List[ScriptSection]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('sections')
    def sections_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Script must have at least one section')
        return v
    
    @validator('total_duration_seconds')
    def validate_total_duration(cls, v, values):
        if 'sections' in values:
            calculated_duration = sum(section.duration_seconds for section in values['sections'])
            if abs(v - calculated_duration) > 30:  # Allow 30 second tolerance
                raise ValueError('Total duration does not match sum of section durations')
        return v


class AudioFile(BaseModel):
    """Generated audio file information"""
    file_path: str
    duration_seconds: int
    file_size_bytes: int
    sample_rate: int
    format: str
    bitrate: Optional[str] = None


class VideoFile(BaseModel):
    """Generated video file information"""
    file_path: str
    duration_seconds: int
    file_size_bytes: int
    resolution: str
    fps: int
    format: str
    codec: str
    thumbnail_path: Optional[str] = None


class GenerationLog(BaseModel):
    """Log entry for generation process"""
    step: str
    status: str
    message: str
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """System performance metrics"""
    metric_name: str
    metric_value: float
    metric_unit: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    service: str
    version: str
    details: Optional[Dict[str, Any]] = None


class OllamaGenerateRequest(BaseModel):
    """Request model for Ollama API"""
    model: str
    prompt: str
    stream: bool = False
    options: Dict[str, Any] = Field(default_factory=dict)


class OllamaGenerateResponse(BaseModel):
    """Response model from Ollama API"""
    model: str
    created_at: datetime
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str = Field(..., min_length=1, max_length=10000)
    voice_speed: float = Field(1.0, ge=0.5, le=2.0)
    output_format: str = Field("wav", regex="^(wav|mp3)$")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None