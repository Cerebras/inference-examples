from typing import Optional

from pydantic import BaseModel

from .globals import CopyPlugin, copy_plugins


class PressRelease(BaseModel):
    title: str
    image: Optional[str]


copy_plugins["PRESS_RELEASE"] = CopyPlugin(
    name="Press Release",
    metadata_class=PressRelease,
    content_class="md",
    title_key="title",
)
