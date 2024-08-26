from enum import Enum

from fireworks.client import AsyncFireworks, Fireworks

from .base_engine import AsyncLLMEngine, LLMEngine


class SUPPORTED_MODELS(Enum):
    LLAMA_V3P1_70B_INSTRUCT = "accounts/fireworks/models/llama-v3p1-70b-instruct"


class FireworksEngine(LLMEngine):
    """
    A concrete implementation of LLMEngine for interacting with Fireworks models.

    This class provides a synchronous interface for querying Fireworks language models.

    Attributes:
        model (str): The name of the Fireworks model to use.
        client (Fireworks): An instance of the Fireworks client for API interactions.

    Inherits from:
        LLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the FireworksEngine.

        Args:
            model (str): The name of the Fireworks model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_V3P1_70B_INSTRUCT.value
        self.client = Fireworks()

    def query(self, **kwargs):
        """
        Send a query to the Fireworks language model.

        This method creates a chat completion using the specified Fireworks model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Fireworks API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = self.client.chat.completions.create(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content


class AsyncFireworksEngine(AsyncLLMEngine):
    """
    An asynchronous implementation of LLMEngine for interacting with Fireworks models.

    This class provides an asynchronous interface for querying Fireworks language models.

    Attributes:
        model (str): The name of the Fireworks model to use.
        client (AsyncFireworks): An instance of the asynchronous Fireworks client for API interactions.

    Inherits from:
        AsyncLLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the AsyncFireworksEngine.

        Args:
            model (str): The name of the Fireworks model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_V3P1_70B_INSTRUCT.value
        self.client = AsyncFireworks()

    async def query(self, **kwargs):
        """
        Asynchronously send a query to the Fireworks language model.

        This method creates a chat completion using the specified Fireworks model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Fireworks API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = await self.client.chat.completions.acreate(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content
