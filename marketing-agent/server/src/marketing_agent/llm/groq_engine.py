from enum import Enum

from groq import AsyncGroq, Groq

from .base_engine import AsyncLLMEngine, LLMEngine


class SUPPORTED_MODELS(Enum):
    LLAMA_3_1_70B_VERSATILE = "llama-3.1-70b-versatile"
    LLAMA_3_1_8B_INSTANT = "llama-3.1-8b-instant"


class GroqEngine(LLMEngine):
    """
    A concrete implementation of LLMEngine for interacting with Groq models.

    This class provides a synchronous interface for querying Groq language models.

    Attributes:
        model (str): The name of the Groq model to use.
        client (Groq): An instance of the Groq client for API interactions.

    Inherits from:
        LLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the GroqEngine.

        Args:
            model (str): The name of the Groq model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_3_1_70B_VERSATILE.value
        self.client = Groq()

    def query(self, **kwargs):
        """
        Send a query to the Groq language model.

        This method creates a chat completion using the specified Groq model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Groq API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = self.client.chat.completions.create(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content


class AsyncGroqEngine(AsyncLLMEngine):
    """
    An asynchronous implementation of LLMEngine for interacting with Groq models.

    This class provides an asynchronous interface for querying Groq language models.

    Attributes:
        model (str): The name of the Groq model to use.
        client (AsyncGroq): An instance of the asynchronous Groq client for API interactions.

    Inherits from:
        AsyncLLMEngine
    """

    def __init__(self, model: str | None = None, *args, **kwargs):
        """
        Initialize the AsyncGroqEngine.

        Args:
            model (str): The name of the Groq model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model or SUPPORTED_MODELS.LLAMA_3_1_70B_VERSATILE.value
        self.client = AsyncGroq()

    async def query(self, **kwargs):
        """
        Asynchronously send a query to the Groq language model.

        This method creates a chat completion using the specified Groq model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Groq API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = await self.client.chat.completions.create(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content
