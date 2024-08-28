from typing import List, Optional
from pydantic import BaseModel, Field

from .globals import copy_plugins, CopyPlugin


class GithubProject(BaseModel):
    project_name: str


copy_plugins["GITHUB_PROJECT"] = CopyPlugin(
    name="GitHub Project README", metadata_class=GithubProject, content_class="md"
)
