import os
from enum import Enum

import httpx

from .base_engine import AsyncLLMEngine, LLMEngine


class SUPPORTED_MODELS(Enum):
    LLAMA_3_1_SONAR_LARGE_128K_ONLINE = "llama-3.1-sonar-large-128k-online"


class PerplexityEngine(LLMEngine):
    """
    A concrete implementation of LLMEngine for interacting with Perplexity AI models.

    This class provides a synchronous interface for querying Perplexity AI language models.

    Attributes:
        model (str): The name of the Perplexity AI model to use.
        apikey (str): The API key for authenticating with Perplexity AI, retrieved from environment variables.

    Inherits from:
        LLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the PerplexityEngine.

        Args:
            model (str): The name of the Perplexity AI model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_3_1_SONAR_LARGE_128K_ONLINE.value
        self.apikey = os.environ["PERPLEXITY_API_KEY"]

    def query(self, **kwargs):
        """
        Send a query to the Perplexity AI language model.

        This method creates a chat completion using the specified Perplexity AI model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Perplexity AI API call.

        Returns:
            str: The content of the first message in the model's response.

        Raises:
            httpx.HTTPError: If there's an issue with the HTTP request.
        """
        url = "https://api.perplexity.ai/chat/completions"

        payload = {
            "model": self.model,
            "return_citations": True,
            **kwargs,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.apikey}",
        }

        response = httpx.post(url, json=payload, headers=headers)

        content = response.json()["choices"][0]["message"]["content"]
        return content


class AsyncPerplexityEngine(AsyncLLMEngine):
    """
    An asynchronous implementation of LLMEngine for interacting with Perplexity AI models.

    This class provides an asynchronous interface for querying Perplexity AI language models.

    Attributes:
        model (str): The name of the Perplexity AI model to use.
        apikey (str): The API key for authenticating with Perplexity AI, retrieved from environment variables.

    Inherits from:
        AsyncLLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the AsyncPerplexityEngine.

        Args:
            model (str): The name of the Perplexity AI model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_3_1_SONAR_LARGE_128K_ONLINE.value
        self.apikey = os.environ["PERPLEXITY_API_KEY"]

    async def query(self, **kwargs):
        """
        Asynchronously send a query to the Perplexity AI language model.

        This method creates a chat completion using the specified Perplexity AI model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Perplexity AI API call.

        Returns:
            str: The content of the first message in the model's response.

        Raises:
            httpx.HTTPError: If there's an issue with the HTTP request.
            KeyError: If the expected data is not found in the API response.
        """
        url = "https://api.perplexity.ai/chat/completions"

        payload = {
            "model": self.model,
            "return_citations": True,
            **kwargs,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.apikey}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=None
            )

        content = response.json()["choices"][0]["message"]["content"]
        return content
