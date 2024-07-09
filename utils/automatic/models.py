from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# Automatic
class SourceNode(BaseModel):
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    file_source: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    gcsBucket: Optional[str] = None
    gcsBucketFolder: Optional[str] = None
    gcsProjectId: Optional[str] = None
    awsAccessKeyId: Optional[str] = None
    node_count: Optional[int] = None
    relationship_count: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    processing_time: float = None
    error_message: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    language: Optional[str] = None
    is_cancelled: bool = None
    processed_chunk: Optional[int] = None
    access_token: Optional[str] = None

# Custom
