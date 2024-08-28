from typing import List, Optional
from pydantic import BaseModel, Field

from .globals import copy_plugins, CopyPlugin


class Tweet(BaseModel):
    tweet: str


class Tweets(BaseModel):
    tweets: List[Tweet]


class TwitterThread(BaseModel):
    image_description: Optional[str] = Field(
        ..., description="Describe a catchy image to include in the thread."
    )
    hashtags: List[str]
    mentions: List[str]


copy_plugins["TWITTER_THREAD"] = CopyPlugin(
    name="Twitter Thread", metadata_class=TwitterThread, content_class=Tweets
)
