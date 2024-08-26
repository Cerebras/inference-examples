from pydantic import BaseModel

from .globals import CopyPlugin, copy_plugins


class GithubProject(BaseModel):
    project_name: str


copy_plugins["GITHUB_PROJECT"] = CopyPlugin(
    name="GitHub Project README",
    metadata_class=GithubProject,
    content_class="md",
    title_key="project_name",
)
