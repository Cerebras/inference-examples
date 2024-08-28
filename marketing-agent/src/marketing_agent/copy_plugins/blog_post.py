from typing import Optional
from pydantic import BaseModel

from .globals import copy_plugins, CopyPlugin


class BlogPost(BaseModel):
    title: str
    subtitle: str
    image_description: Optional[str]


copy_plugins["BLOG_POST"] = CopyPlugin(
    name="Blog Post", metadata_class=BlogPost, content_class="md"
)
