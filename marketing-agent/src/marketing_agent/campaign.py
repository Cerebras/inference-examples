import asyncio
import os
import traceback
from collections import defaultdict
from enum import Enum
from typing import Union

import yaml
from pydantic import BaseModel

from .datatypes import (Audience, AudienceUnion, Channel, CopyStrategy, Market,
                        ProductAngle)
from .llm.base_engine import AsyncLLMEngine
from .marketing_copy import CopyPiece

# Use this to ensure that each copy gets a unique filename
_copy_counters = defaultdict(int)
FULLY_PARALLEL = os.environ.get("FULLY_PARALLEL", False)


class StatusMessageType(Enum):
    """
    Enum class to represent different types of status messages.

    Attributes:
        STATUS: Represents a general status update message.
        FILE_CREATED: Represents a message indicating a file has been created. The
                      corresponding message includes 'filename' and 'content' keys.
    """

    STATUS = "STATUS"
    FILE_CREATED = "FILE_CREATED"


def _submit_copy(
    feed: asyncio.Queue,
    channel: Channel,
    metadata: BaseModel,
    content: Union[str, BaseModel],
):
    """
    Submit generated copy to the feed queue.

    Args:
        feed (asyncio.Queue): The queue to submit status messages to.
        channel (Channel): The marketing channel for the copy.
        metadata (BaseModel): The metadata for the copy.
        content (Union[str, BaseModel]): The content of the copy.
    """
    global _copy_counters

    if metadata == None and content == None:
        return

    _copy_counters[channel.name] += 1
    filename = f"{channel.name}-{_copy_counters[channel.name]}"

    if metadata != None:
        feed.put_nowait(
            (
                StatusMessageType.FILE_CREATED,
                {
                    "filename": f"{filename}-metadata.yaml",
                    "content": yaml.dump(metadata.model_dump()),
                },
            )
        )

    if content != None:
        if isinstance(content, str):
            feed.put_nowait(
                (
                    StatusMessageType.FILE_CREATED,
                    {"filename": f"{filename}-content.md", "content": content},
                )
            )
        else:
            feed.put_nowait(
                (
                    StatusMessageType.FILE_CREATED,
                    {
                        "filename": f"{filename}-content.yaml",
                        "content": yaml.dump(content.model_dump()),
                    },
                )
            )


class Campaign:
    def __init__(
        self,
        reasoning_llm: AsyncLLMEngine,
        search_llm: AsyncLLMEngine,
        product_description: str,
        num_revisions: int,
        feed: asyncio.Queue,
    ):
        self.reasoning_llm = reasoning_llm
        self.search_llm = search_llm
        self.product_description = product_description
        self.num_revisions = num_revisions
        self.feed = feed

    async def create_copy_for_strategy(
        self,
        angle: ProductAngle,
        audience: Audience,
        channel: Channel,
        copy_strategy: CopyStrategy,
    ):
        """
        Create & iterate on copy for a specific marketing strategy.

        Args:
            angle (ProductAngle): The marketing angle for the product.
            audience (Audience): The target audience.
            channel (Channel): The marketing channel.
            copy_strategy (CopyStrategy): The strategy for creating the copy.
        """
        global _copy_counters

        try:
            copy = CopyPiece(
                self.reasoning_llm,
                self.product_description,
                angle,
                audience,
                channel,
                copy_strategy,
            )
        except ValueError:
            print(f"Copy type not supported for {channel.copy_format}")
            return

        self.feed.put_nowait(
            (StatusMessageType.STATUS, f"Creating copy for {channel.name} marketing")
        )

        try:
            await copy.initialize()
            for _ in range(self.num_revisions):
                await copy.improve()
        except:
            traceback.print_exc()
            return

        _submit_copy(self.feed, channel, copy.metadata, copy.content)

    async def create_copy_for_channel(
        self,
        angle: ProductAngle,
        market: Market,
        audience: Audience,
        channel: Channel,
    ):
        """
        Generate a copy strategy for a specific channel and create the corresponding copy.

        Args:
            angle (ProductAngle): The marketing angle for the product.
            market (Market): The target market.
            audience (Audience): The target audience.
            channel (Channel): The marketing channel.
        """

        # Understand what copy is appropriate for each audience & channel
        try:
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    (
                        f"Generating strategy and evaluation criteria for {channel.name} "
                        f"marketing"
                    ),
                )
            )

            strategy = await self.reasoning_llm.query_object(
                CopyStrategy,
                PROBLEM_STATEMENT=angle.problem_addressed,
                VALUE_PROPOSITION=angle.value_proposition,
                MARKETS=yaml.dump(market.model_dump()),
                DEMOGRAPHICS=yaml.dump(audience.demographics),
                CHANNEL=channel.name,
                COPY_FORMAT=channel.copy_format,
                TASK=(
                    "Generate a strategy for generating a COPY_FORMAT for the "
                    "VALUE_PROPOSITION targeting the DEMOGRAPHICS through the CHANNEL. "
                    "Suggest whatever content format is appropriate for the CHANNEL, "
                    "and suggest review criteria for making sure COPY_FORMAT is good."
                ),
            )
        except:
            traceback.print_exc()
            return

        await self.create_copy_for_strategy(angle, audience, channel, strategy)

    async def create_copy_for_market_audience(
        self,
        angle: ProductAngle,
        market: Market,
        audience: Audience,
    ):
        """
        Identify suitable channels and create copy for a specific market and audience
        combination.

        Args:
            angle (ProductAngle): The marketing angle for the product.
            market (Market): The target market.
            audience (Audience): The target audience.
        """

        # Identify suitable channels for reaching the audience in the market
        class Response(BaseModel):
            channels: list[Channel]

        self.feed.put_nowait(
            (
                StatusMessageType.STATUS,
                (
                    f"Identifying candidate channels for reaching the {audience.profile} "
                    f"audience in the {market.market_description} market with value "
                    f"proposition: {angle.value_proposition}"
                ),
            )
        )

        try:
            response = await self.reasoning_llm.query_object(
                Response,
                VALUE_PROPOSITION=angle.value_proposition,
                AUDIENCE_PROFILE=audience.profile,
                MARKET=market,
                DEMOGRAPHICS=yaml.dump(audience.demographics),
                TASK=(
                    "Suggest some channels for reaching the DEMOGRAPHICS with "
                    "VALUE_PROPOSITION in MARKET. Include various social media and "
                    "physical channels where appropriate."
                ),
            )
        except:
            traceback.print_exc()
            return

        # Generate copy for each channel
        tasks = []
        for channel in response.channels:
            tasks.append(self.create_copy_for_channel(angle, market, audience, channel))

        if FULLY_PARALLEL:
            await asyncio.gather(*tasks)
        else:
            for task in tasks:
                await task

    async def generate_market_analysis(self, angle: ProductAngle) -> list[Market]:
        """
        Generate a market analysis for a given product angle.

        Args:
            angle (ProductAngle): The marketing angle for the product.

        Returns:
            list[Market]: A list of potential markets for the product.

        Raises an exception if the reasoning engine fails to return a response.
        """

        # Identify candidate markets for the value proposition
        class Response(BaseModel):
            markets: list[Market]

        self.feed.put_nowait(
            (
                StatusMessageType.STATUS,
                (
                    f"Identifying candidate markets for value proposition: "
                    f"{angle.value_proposition}"
                ),
            )
        )

        response = await self.search_llm.query_object(
            Response,
            VALUE_PROPOSITION=angle.value_proposition,
            USAGE_MODEL=angle.usage,
            TASK=(
                "Using available market research, suggest some markets where "
                "VALUE_PROPOSITION through USAGE_MODEL would be useful."
            ),
        )

        # No need to normalize the markets. Return as is.
        return response.markets

    async def generate_audience_analysis(self, angle: ProductAngle) -> list[Audience]:
        """
        Generate an audience analysis for a given product angle.

        Args:
            angle (ProductAngle): The marketing angle for the product.

        Returns:
            list[Audience]: A list of potential target audiences for the product.

        Raises an exception if the reasoning engine fails to return a response.
        """

        # Identify candidate audiences for the value proposition
        class Response(BaseModel):
            audiences: list[AudienceUnion]

        self.feed.put_nowait(
            (
                StatusMessageType.STATUS,
                (
                    f"Identifying candidate audiences for value proposition: "
                    f"{angle.value_proposition}"
                ),
            )
        )

        response = await self.reasoning_llm.query_object(
            Response,
            PROBLEM_STATEMENT=angle.problem_addressed,
            USAGE=angle.usage,
            TASK=(
                "Suggest some target audiences for the PROBLEM_STATEMENT with the "
                "USAGE model."
            ),
        )

        # Normalize the audience types to the Audience class
        return [x.normalize() for x in response.audiences]

    async def create_copy_for_angle(self, angle: ProductAngle):
        """
        Create copy for a specific product angle across various markets and audiences.

        Args:
            feed (asyncio.Queue): The queue to submit status messages to.
            angle (ProductAngle): The marketing angle for the product.

        Returns:
            tuple[list[Market], list[Audience]]: A tuple containing lists of identified
                                                markets and audiences.
        """
        # Identify candidate markets and audiences for the value proposition
        try:
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    (
                        f"Identifying candidate markets and audiences for value "
                        f"proposition: {angle.value_proposition}"
                    ),
                )
            )
            known_markets, audiences = await asyncio.gather(
                self.generate_market_analysis(angle),
                self.generate_audience_analysis(angle),
            )
        except:
            traceback.print_exc()
            return

        # Generate copy for each market and audience
        tasks = []
        for market in known_markets:
            for audience in audiences:
                tasks.append(
                    self.create_copy_for_market_audience(angle, market, audience)
                )

        if FULLY_PARALLEL:
            await asyncio.gather(*tasks)
        else:
            for task in tasks:
                await task

    async def generate(self):
        """
        Generate a complete marketing campaign for a given product description.

        This function generates multiple angles for the product and creates copy for each
        angle across various markets and audiences.

        Args:
            feed (asyncio.Queue): The queue to submit status messages to.
        """

        # Get candidate angles for the product description
        class Response(BaseModel):
            candidates: list[ProductAngle]

        try:
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    "Generating candidate value propositions for the marketing campaign",
                )
            )
            response = await self.reasoning_llm.query_object(
                Response,
                PRODUCT_DESCRIPTION=self.product_description,
                TASK="List some candidate angles for PRODUCT_DESCRIPTION.",
            )
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    f"Generated {len(response.candidates)} candidate angles",
                )
            )
        except:
            traceback.print_exc()
            return

        product_angles = response.candidates

        # Generate copy for each angle
        await asyncio.gather(
            *[self.create_copy_for_angle(x) for x in product_angles],
        )
