"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal

# Core entities for the AI Shorts Automation

class Account(BaseModel):
    """
    Connected social account tokens/metadata
    Collection name: "account"
    """
    platform: Literal["youtube", "tiktok", "instagram"] = Field(..., description="Platform type")
    account_name: Optional[str] = Field(None, description="Readable account label")
    access_token: Optional[str] = Field(None, description="OAuth access token (encrypted at rest in production)")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    expires_at: Optional[int] = Field(None, description="Epoch seconds when token expires")
    connected: bool = Field(default=False, description="Whether the account is connected")

class VideoJob(BaseModel):
    """
    A job to create and optionally auto-post a short video from Reddit content
    Collection name: "videojob"
    """
    title: Optional[str] = Field(None, description="Optional custom title for the video")
    subreddit: Optional[str] = Field(None, description="Subreddit to pull content from")
    reddit_post_url: Optional[HttpUrl] = Field(None, description="Specific Reddit post URL")
    keyword: Optional[str] = Field(None, description="Keyword/topic to search on Reddit")

    voice: Literal["female-soft", "female-energetic", "male-calm", "male-dramatic"] = Field(
        default="female-soft", description="TTS voice preset"
    )
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = Field(default="9:16", description="Output aspect ratio")
    include_captions: bool = Field(default=True, description="Burn captions into video")
    include_broll: bool = Field(default=True, description="Auto add b-roll and sound effects")

    autopost_youtube: bool = Field(default=False)
    autopost_tiktok: bool = Field(default=False)
    autopost_instagram: bool = Field(default=False)

    status: Literal["queued", "processing", "completed", "failed"] = Field(default="queued")
    error: Optional[str] = None
    result_video_url: Optional[HttpUrl] = None
    platforms_posted: List[str] = Field(default_factory=list)
