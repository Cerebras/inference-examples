# Enums
from dataclasses import dataclass
from typing import Literal, Union

from pydantic import BaseModel


@dataclass
class CopyPlugin:
    name: str
    metadata_class: Union[type[BaseModel], str]
    content_class: Union[type[BaseModel], str]


copy_plugins: dict[str, CopyPlugin] = {}
