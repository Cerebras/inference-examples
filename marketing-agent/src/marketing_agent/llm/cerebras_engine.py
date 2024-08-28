from cerebras.cloud.sdk import AsyncCerebras, Cerebras

from .base_engine import AsyncLLMEngine, LLMEngine


class CerebrasEngine(LLMEngine):
    """
    A concrete implementation of LLMEngine for interacting with Cerebras models.

    This class provides a synchronous interface for querying Cerebras language models.

    Attributes:
        model (str): The name of the Cerebras model to use.
        client (Cerebras): An instance of the Cerebras client for API interactions.

    Inherits from:
        LLMEngine
    """

    def __init__(self, model: str, *args, **kwargs):
        """
        Initialize the CerebrasEngine.

        Args:
            model (str): The name of the Cerebras model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.client = Cerebras()

    def query(self, **kwargs):
        """
        Send a query to the Cerebras language model.

        This method creates a chat completion using the specified Cerebras model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Cerebras API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = self.client.chat.completions.create(model=self.model, **kwargs)
        return response.choices[0].message.content


class AsyncCerebrasEngine(AsyncLLMEngine):
    """
    An asynchronous implementation of LLMEngine for interacting with Cerebras models.

    This class provides an asynchronous interface for querying Cerebras language models.

    Attributes:
        model (str): The name of the Cerebras model to use.
        client (AsyncCerebras): An instance of the asynchronous Cerebras client for API interactions.

    Inherits from:
        AsyncLLMEngine
    """

    def __init__(self, model: str, *args, **kwargs):
        """
        Initialize the AsyncCerebrasEngine.

        Args:
            model (str): The name of the Cerebras model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.client = AsyncCerebras()

    async def query(self, **kwargs):
        """
        Asynchronously send a query to the Cerebras language model.

        This method creates a chat completion using the specified Cerebras model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Cerebras API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = await self.client.chat.completions.create(model=self.model, **kwargs)
        return response.choices[0].message.content
