from typing import List, Optional
from pydantic import BaseModel

from .globals import copy_plugins, CopyPlugin


class YoutubeVideo(BaseModel):
    title: str
    description: str
    tags: List[str]
    thumbnail_description: Optional[str]


copy_plugins["VIDEO_SCRIPT"] = CopyPlugin(
    name="Youtube video script", metadata_class=YoutubeVideo, content_class="md"
)
