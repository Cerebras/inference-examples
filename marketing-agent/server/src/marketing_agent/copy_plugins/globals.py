# Enums
from dataclasses import dataclass
from typing import Union

from pydantic import BaseModel


@dataclass
class CopyPlugin:
    name: str
    title_key: str
    metadata_class: Union[type[BaseModel], str]
    content_class: Union[type[BaseModel], str]


copy_plugins: dict[str, CopyPlugin] = {}
