import json
from abc import ABC, abstractmethod
from typing import TypeVar, Union
from xml.sax.saxutils import escape as xml_escape

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
S = TypeVar("S", bound=Union[str, T])


class LLMEngine(ABC):
    """
    A class representing an engine for interacting with Language Learning Models
    (LLMs).

    This class provides an interface for getting structured outputs.

    Attributes:
        fallback (LLMEngine): An optional fallback LLMEngine to use if queries fail.

    Usage:
        Subclass LLMEngine and implement the `query` method to use with a specific LLM API.
        Use `query_object` to get responses parsed into pydantic object types.
        Use `query_block` to get responses for markdown block types.
    """

    def __init__(self, fallback: "LLMEngine" = None):
        """
        Initialize the LLMEngine.

        Args:
            fallback (LLMEngine, optional): Another LLMEngine instance to use as a fallback
                                            if this engine's queries fail. Defaults to None.
        """
        self.fallback = fallback

    @abstractmethod
    def query(self, **kwargs):
        """
        Send a query to the Language Learning Model.

        This is an abstract method that should be implemented by subclasses to interact
        with specific LLM APIs.

        Args:
            **kwargs: Arbitrary keyword arguments for the query. Example: max_tokens.
        """
        pass

    def query_object(self, response_model: type[T], **kwargs) -> T:
        """
        Query the LLM and parse the response into a specified object type.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages, sends the query, and parses the response.

        Args:
            response_model (type[T]): The type of object to parse the response into. It
                                      should be a Pydantic BaseModel subclass.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            T: An instance of the response_model type, populated with the parsed
               response.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        prompt_args = {k: v for k, v in kwargs.items() if k == k.upper()}
        api_args = {k: v for k, v in kwargs.items() if k != k.upper()}

        try:
            response = self.query(
                messages=generate_obj_query_messages(response_model, prompt_args),
                **api_args,
            )
        except Exception:
            if self.fallback:
                return self.fallback.query_object(response_model, **kwargs)
            else:
                raise

        return parse_obj_response(response_model, response)

    def query_block(self, block_type: str, **kwargs) -> str:
        """
        Query the LLM for a specific block type and parse the response.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages for the specified block type, sends the query,
        and parses the response.

        Args:
            block_type (str): The type of block to query for.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            T: The parsed response for the specified block type.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        prompt_args = {k: v for k, v in kwargs.items() if k == k.upper()}
        api_args = {k: v for k, v in kwargs.items() if k != k.upper()}

        try:
            response = self.query(
                messages=generate_block_query_messages(block_type, prompt_args),
                **api_args,
            )
        except Exception:
            if self.fallback:
                return self.fallback.query_block(block_type, **kwargs)
            else:
                raise

        return parse_block_response(block_type, response)

    def query_structured(self, structure: S, **kwargs):
        """
        Query the LLM and parse the response into a specified structure.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages, sends the query, and parses the response.

        Args:
            structure (Union[str, BaseModel]): The structure to parse the response into,
                                               either a string for markdown block types
                                               or a Pydantic model for object types.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            Union[str, BaseModel]: The parsed response in the specified structure.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        if isinstance(structure, str):
            return self.query_block(structure, **kwargs)
        elif issubclass(structure, BaseModel):
            return self.query_object(structure, **kwargs)
        else:
            raise ValueError(
                f"Invalid structure type. Must be a string or a Pydantic model. Got: {type(structure)}"
            )


class AsyncLLMEngine(ABC):
    """
    A class representing an engine for interacting with Language Learning Models
    (LLMs).

    This class provides an interface for getting structured outputs.

    Attributes:
        fallback (AsyncLLMEngine): An optional fallback AsyncLLMEngine to use if
                                   queries fail.

    Methods:
        query: Abstract method to be implemented by subclasses for sending queries to
               the LLM.
        query_object: Query the LLM and parse the response into a specified object
                      type.
        query_block: Query the LLM for a specific block type and parse the response.

    Usage:
        Subclass AsyncLLMEngine and implement the `query` method to use with a specific
        LLM API.

        Use `query_object` to get responses parsed into pydantic object types.
        Use `query_block` to get responses for markdown block types.
    """

    def __init__(self, fallback: "AsyncLLMEngine" = None):
        """
        Initialize the AsyncLLMEngine.

        Args:
            fallback (AsyncLLMEngine, optional): Another LLMEngine instance to use as a
                                                 fallback if this engine's queries
                                                 fail. Defaults to None.
        """
        self.fallback = fallback

    @abstractmethod
    async def query(self, **kwargs):
        """
        Send a query to the Language Learning Model.

        This is an abstract method that should be implemented by subclasses to interact
        with specific LLM APIs.

        Args:
            **kwargs: Arbitrary keyword arguments for the query. Example: max_tokens.
        """
        pass

    async def query_object(self, response_model: type[T], **kwargs) -> T:
        """
        Query the LLM and parse the response into a specified object type.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages, sends the query, and parses the response.

        Args:
            response_model (type[T]): The type of object to parse the response into. It
                                      should be a Pydantic BaseModel subclass.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            T: An instance of the response_model type, populated with the parsed
               response.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        prompt_args = {k: v for k, v in kwargs.items() if k == k.upper()}
        api_args = {k: v for k, v in kwargs.items() if k != k.upper()}

        try:
            response = await self.query(
                messages=generate_obj_query_messages(response_model, prompt_args),
                **api_args,
            )
        except Exception:
            if self.fallback:
                return await self.fallback.query_object(response_model, **kwargs)
            else:
                raise

        return parse_obj_response(response_model, response)

    async def query_block(self, block_type: str, **kwargs) -> T:
        """
        Query the LLM for a specific block type and parse the response.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages for the specified block type, sends the query,
        and parses the response.

        Args:
            block_type (str): The type of block to query for.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            T: The parsed response for the specified block type.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        prompt_args = {k: v for k, v in kwargs.items() if k == k.upper()}
        api_args = {k: v for k, v in kwargs.items() if k != k.upper()}

        try:
            response = await self.query(
                messages=generate_block_query_messages(block_type, prompt_args),
                **api_args,
            )
        except Exception:
            if self.fallback:
                return await self.fallback.query_block(block_type, **kwargs)
            else:
                raise

        return parse_block_response(block_type, response)

    async def query_structured(self, structure: S, **kwargs) -> S:
        """
        Query the LLM and parse the response into a specified structure.

        This method separates the input kwargs into prompt arguments and API arguments,
        generates the query messages, sends the query, and parses the response.

        Args:
            structure (Union[str, BaseModel]): The structure to parse the response into,
                                               either a string for markdown block types
                                               or a Pydantic model for object types.
            **kwargs: Arbitrary keyword arguments. Arguments with all-uppercase keys
                      will be passed to the LLM via the prompt. Others as LLM API
                      arguments.

        Returns:
            Union[str, BaseModel]: The parsed response in the specified structure.

        Raises:
            Exception: If the query fails and there's no fallback engine.
        """
        if isinstance(structure, str):
            return await self.query_block(structure, **kwargs)
        elif issubclass(structure, BaseModel):
            return await self.query_object(structure, **kwargs)
        else:
            raise ValueError(
                f"Invalid structure type. Must be a string or a Pydantic model. Got: {type(structure)}"
            )


def _normalize(obj):
    """
    Recursively normalize an object for serialization.

    This function handles Pydantic BaseModel instances, dictionaries, and lists.
    Other types are returned as-is.

    Args:
        obj: The object to normalize.

    Returns:
        The normalized version of the object.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize(v) for v in obj]
    else:
        return obj


def _serialize(obj):
    """
    Serialize an object to a JSON string.

    This function first normalizes the object using _normalize(),
    then serializes it to a JSON string with indentation.

    Args:
        obj: The object to serialize.

    Returns:
        str: The JSON string representation of the object.
    """
    return json.dumps(_normalize(obj), indent=2)


def compile_user_prompt(**kwargs):
    """
    Compile a user prompt from keyword arguments.

    Each keyword argument is serialized and wrapped in XML-like tags.

    Args:
        **kwargs: Keyword arguments to include in the prompt.

    Returns:
        str: The compiled user prompt.
    """
    prompt_pieces = []
    for key, value in kwargs.items():
        value = xml_escape(_serialize(value))
        prompt_pieces.append(f"<{key}>{value}</{key}>")

    return "\n\n".join(prompt_pieces)


def _compile_system_prompt(response_model: type[BaseModel]):
    """
    Compile a system prompt for a given response model.

    This function creates a prompt instructing the model to return
    a JSON object matching the schema of the provided response model.

    Args:
        response_model (BaseModel): The Pydantic model to use for the response schema.

    Returns:
        str: The compiled system prompt.
    """
    schema = response_model.model_json_schema()
    return (
        "Your task is to understand the content and provide "
        "the parsed objects in json that matches the following json_schema:\n\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Make sure to return an instance of the JSON, not the schema itself."
    )


def generate_obj_query_messages(response_model: type[BaseModel], prompt_args: dict):
    """
    Generate messages for an object query.

    This function creates a system message and a user message for querying
    an LLM to generate a response matching a specific model.

    Args:
        response_model (BaseModel): The expected response model.
        prompt_args: Arguments to include in the user prompt.

    Returns:
        list: A list of message dictionaries for the LLM query.
    """
    user_prompt = compile_user_prompt(**prompt_args) + (
        "\n\nReturn the correct JSON response within a ```json codeblock, not the "
        "JSON_SCHEMA. Use only fields specified by the JSON_SCHEMA and nothing else."
    )
    system_prompt = _compile_system_prompt(response_model)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_obj_response(response_model: type[BaseModel], content: str):
    """
    Parse an object response from the LLM.

    This function extracts JSON from a code block in the response content
    and constructs an instance of the response model from it.

    Args:
        response_model (BaseModel): The expected response model class.
        content (str): The response content from the LLM.

    Returns:
        An instance of the response model.
    """
    if "```json" in content:
        json_start = content.find("```json") + 7
    elif "```" in content:
        json_start = content.find("```") + 3

    json_end = content.find("```", json_start)
    obj = json.loads(content[json_start:json_end].strip())

    return response_model(**obj)


def generate_block_query_messages(block_type: str, prompt_args):
    """
    Generate messages for a block query.

    This function creates a system message and a user message for querying
    an LLM to generate a response in a specific block format.

    Args:
        block_type (str): The type of block to generate (e.g., "python", "sql").
        prompt_args: Arguments to include in the user prompt.

    Returns:
        list: A list of message dictionaries for the LLM query.
    """
    prompt = compile_user_prompt(**prompt_args)
    system_prompt = (
        "Respond with a single fenced code block and nothing else. Provide "
        f"the response within: ```{block_type}\ncontent\n```.\n\n"
        f"The content should be {block_type}-formatted."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]


def parse_block_response(block_type: str, content: str):
    """
    Parse a block response from the LLM.

    This function extracts the content from a code block of the specified type
    in the response content.

    Args:
        block_type (str): The type of block to extract (e.g., "python", "sql").
        content (str): The response content from the LLM.

    Returns:
        str: The extracted content from the code block.
    """
    start = content.rfind(f"```{block_type}") + 3 + len(block_type)
    end = content.find("```", start)

    return content[start:end].strip()
