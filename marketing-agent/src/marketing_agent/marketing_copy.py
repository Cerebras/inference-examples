from typing import List, Optional, Union

import yaml
from pydantic import BaseModel

from .copy_plugins.globals import copy_plugins
from .datatypes import Audience, Channel, CopyStrategy, ProductAngle
from .llm.base_engine import AsyncLLMEngine


class CopyPiece:
    """
    Represents a piece of copy content for marketing purposes.

    This class handles the generation and improvement of copy content
    using an LLM (Language Learning Model).

    Attributes:
        metadata: The generated metadata for the copy.
        content: The generated content for the copy.
    """

    def __init__(
        self,
        llm: AsyncLLMEngine,
        product: str,
        angle: ProductAngle,
        audience: Audience,
        channel: Channel,
        copy_strategy: CopyStrategy,
    ):
        """
        Initialize a new Copy instance.

        Args:
            llm (AsyncLLMEngine): The asynchronous LLM engine for generating content.
            product (str): The product being marketed.
            angle (ProductAngle): The product angle for marketing.
            audience (Audience): The target audience.
            channel (Channel): The associated marketing channel.
            copy_strategy (CopyStrategy): The strategy for creating the copy.

        Raises:
            ValueError: If the channel's copy type is not supported.
        """

        if channel.copy_format not in copy_plugins:
            raise ValueError(f"Copy type not supported for {channel.copy_format}")

        self._llm = llm
        self._product = product
        self._angle = angle
        self._audience = audience
        self._channel = channel
        self._strategy = copy_strategy
        self.metadata = None
        self.content = None

        # Retrieve the copy classes based on the channel's copy format
        self.plugin = copy_plugins[channel.copy_format]

    async def initialize(self):
        """
        Asynchronously generate initial metadata and content for the copy.

        This method uses the LLM to generate metadata and content based on
        the initialized attributes of the Copy instance.

        The generated metadata and content are stored in the instance attributes.
        """

        # Generate the metadata
        metadata = await self._llm.query_structured(
            self.plugin.metadata_class,
            PROBLEM_STATEMENT=self._angle.problem_addressed,
            VALUE_PROPOSITION=self._angle.value_proposition,
            AUDIENCE_PROFILE=self._audience.profile,
            DEMOGRAPHICS=yaml.dump(self._audience.demographics),
            STRATEGY=self._strategy.strategy,
            PRODUCT_POSITIONING=self._strategy.product_positioning,
            COMPETITIVE_CLAIM=self._strategy.competitive_claim,
            TASK=(
                f"Generate a {self.plugin.name} for the PROBLEM_STATEMENT and "
                "VALUE_PROPOSITION targeting the AUDIENCE_PROFILE with "
                "the DEMOGRAPHICS."
            ),
        )

        if isinstance(metadata, str):
            metadata_string = metadata
        elif isinstance(metadata, BaseModel):
            metadata_string = yaml.dump(metadata.model_dump())

        # Generate the content
        content = await self._llm.query_structured(
            self.plugin.content_class,
            PROBLEM_STATEMENT=self._angle.problem_addressed,
            VALUE_PROPOSITION=self._angle.value_proposition,
            AUDIENCE_PROFILE=self._audience.profile,
            DEMOGRAPHICS=yaml.dump(self._audience.demographics),
            STRATEGY=self._strategy.strategy,
            PRODUCT_POSITIONING=self._strategy.product_positioning,
            COMPETITIVE_CLAIM=self._strategy.competitive_claim,
            METADATA=metadata_string,
            TASK=(
                f"Generate a {self.plugin.name} with METADATA for the PROBLEM_STATEMENT "
                "and VALUE_PROPOSITION targeting the AUDIENCE_PROFILE with the "
                "DEMOGRAPHICS."
            ),
        )

        self.metadata = metadata
        self.content = content

    async def improve(self):
        """
        Asynchronously improve the existing metadata and content of the copy.

        This method evaluates the current metadata and content, then uses the LLM
        to generate improved versions based on the evaluation.

        The improved metadata and content replace the existing ones in the instance attributes.
        """

        class Evaluation(BaseModel):
            pros: List[str]
            cons: List[str]
            suggestions: List[str]

        evaluation = await self._llm.query_object(
            Evaluation,
            PRODUCT=self._product,
            METADATA=self.metadata,
            CONTENT=self.content,
            TASK=(
                f"The METADATA and CONTENT are for a {self.plugin.name} for Evaluate the "
                "METADATA and CONTENT. List the pros and cons of each. Then suggest "
                "improvements."
            ),
        )

        # Generate the updated metadata
        metadata = await self._llm.query_structured(
            self.plugin.metadata_class,
            PROBLEM_STATEMENT=self._angle.problem_addressed,
            VALUE_PROPOSITION=self._angle.value_proposition,
            AUDIENCE_PROFILE=self._audience.profile,
            DEMOGRAPHICS=yaml.dump(self._audience.demographics),
            STRATEGY=self._strategy.strategy,
            PRODUCT_POSITIONING=self._strategy.product_positioning,
            COMPETITIVE_CLAIM=self._strategy.competitive_claim,
            METADATA=self.metadata,
            EVALUATION=evaluation,
            TASK=(
                f"The METADATA describes a {self.plugin.name}. Improve the METADATA based on the "
                "EVALUATION."
            ),
        )

        if isinstance(metadata, str):
            metadata_string = metadata
        elif isinstance(metadata, BaseModel):
            metadata_string = yaml.dump(metadata.model_dump())

        # Generate the updated content
        content = await self._llm.query_structured(
            self.plugin.content_class,
            PROBLEM_STATEMENT=self._angle.problem_addressed,
            VALUE_PROPOSITION=self._angle.value_proposition,
            AUDIENCE_PROFILE=self._audience.profile,
            DEMOGRAPHICS=yaml.dump(self._audience.demographics),
            STRATEGY=self._strategy.strategy,
            PRODUCT_POSITIONING=self._strategy.product_positioning,
            COMPETITIVE_CLAIM=self._strategy.competitive_claim,
            METADATA=metadata_string,
            EVALUATION=evaluation,
            CONTENT=self.content,
            TASK=(
                f"The CONTENT is for a {self.plugin.name} with METADATA. Improve the CONTENT "
                "based on the EVALUATION."
            ),
        )

        self.metadata = metadata
        self.content = content
