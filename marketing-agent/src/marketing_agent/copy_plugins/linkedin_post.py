from typing import List, Optional
from pydantic import BaseModel

from .globals import copy_plugins, CopyPlugin


class LinkedInPost(BaseModel):
    title: str
    hashtags: List[str]
    mentions: List[str]
    image_description: Optional[str]


copy_plugins["LINKEDIN_POST"] = CopyPlugin(
    name="LinkedIn Post", metadata_class=LinkedInPost, content_class="md"
)
