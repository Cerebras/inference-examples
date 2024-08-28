from together import AsyncTogether, Together

from .base_engine import AsyncLLMEngine, LLMEngine


class TogetherEngine(LLMEngine):
    """
    A concrete implementation of LLMEngine for interacting with Together models.

    This class provides a synchronous interface for querying Together language models.

    Attributes:
        model (str): The name of the Together model to use.
        client (Together): An instance of the Together client for API interactions.

    Inherits from:
        LLMEngine
    """

    def __init__(self, model: str, *args, **kwargs):
        """
        Initialize the TogetherEngine.

        Args:
            model (str): The name of the Together model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.client = Together()

    def query(self, **kwargs):
        """
        Send a query to the Together language model.

        This method creates a chat completion using the specified Together model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Together API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = self.client.chat.completions.create(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content


class AsyncTogetherEngine(AsyncLLMEngine):
    """
    An asynchronous implementation of LLMEngine for interacting with Together models.

    This class provides an asynchronous interface for querying Together language models.

    Attributes:
        model (str): The name of the Together model to use.
        client (AsyncTogether): An instance of the asynchronous Together client for API interactions.

    Inherits from:
        AsyncLLMEngine
    """

    def __init__(self, model: str, *args, **kwargs):
        """
        Initialize the AsyncTogetherEngine.

        Args:
            model (str): The name of the Together model to use.
            *args: Variable length argument list to pass to the parent constructor.
            **kwargs: Arbitrary keyword arguments to pass to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.client = AsyncTogether()

    async def query(self, **kwargs):
        """
        Asynchronously send a query to the Together language model.

        This method creates a chat completion using the specified Together model
        and returns the content of the first message in the response.

        Args:
            **kwargs: Arbitrary keyword arguments to pass to the Together API call.

        Returns:
            str: The content of the first message in the model's response.
        """
        response = await self.client.chat.completions.create(
            model=self.model, stream=False, **kwargs
        )
        return response.choices[0].message.content
