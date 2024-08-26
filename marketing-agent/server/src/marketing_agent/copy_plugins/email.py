from typing import List

from pydantic import BaseModel

from .globals import CopyPlugin, copy_plugins


class Email(BaseModel):
    subject: str
    attachment_descriptions: List[str]


copy_plugins["EMAIL"] = CopyPlugin(
    name="Email", metadata_class=Email, content_class="md", title_key="subject"
)
