from typing import List
from pydantic import BaseModel, Field

from .globals import copy_plugins, CopyPlugin


class Email(BaseModel):
    subject: str
    attachment_descriptions: List[str]


copy_plugins["EMAIL"] = CopyPlugin(
    name="Email", metadata_class=Email, content_class="md"
)
