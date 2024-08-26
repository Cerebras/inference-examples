from typing import List, Optional

from pydantic import BaseModel, Field

from .globals import CopyPlugin, copy_plugins


class Tweet(BaseModel):
    hook: str
    tweet: str
    image_description: Optional[str] = Field(
        ..., description="Describe a catchy image to include in the thread."
    )
    hashtags: List[str]
    mentions: List[str]


copy_plugins["TWEET"] = CopyPlugin(
    name="Tweet",
    metadata_class=Tweet,
    content_class="md",
    title_key="hook",
)
