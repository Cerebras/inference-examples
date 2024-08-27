import asyncio
import json
import logging
import os
import traceback
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel

from .datatypes import (
    Audience,
    AudienceUnion,
    Channel,
    CopyStrategy,
    Market,
    ProductAngle,
)
from .llm.base_engine import AsyncLLMEngine
from .marketing_copy import CopyPiece

logger = logging.getLogger(__name__)

# Use this to ensure that each copy gets a unique filename
_copy_counters = defaultdict(int)
FULLY_PARALLEL = os.environ.get("FULLY_PARALLEL", False)


class StatusMessageType(Enum):
    """
    Enum class to represent different types of status messages.

    Attributes:
        STATUS: Represents a general status update message.
        RESOURCE_CREATED: Represents a message indicating a new resource has been created. The
                          corresponding message includes 'resource_type', 'filename',
                          'content', and 'metadata' keys.
    """

    STATUS = "STATUS"
    RESOURCE_CREATED = "RESOURCE_CREATED"


def _submit_copy(
    feed: asyncio.Queue,
    copy_piece: CopyPiece,
):
    """
    Submit generated copy to the feed queue.

    Args:
        feed (asyncio.Queue): The queue to submit status messages to.
        channel (Channel): The marketing channel for the copy.
        copy_piece (CopyPiece): The copy piece to submit.
    """
    global _copy_counters

    if not copy_piece.metadata and not copy_piece.content:
        return

    content_type = copy_piece._metadata_class.__name__
    # like "LinkedIn Sponsored Content
    _copy_counters[content_type] += 1
    metadata = copy_piece.metadata.model_dump()
    title = metadata.get(copy_piece._title_key, content_type)
    stringified_content = (
        copy_piece.content
        if isinstance(copy_piece.content, str)
        else json.dumps(copy_piece.content.model_dump())
    )
    feed.put_nowait(
        (
            StatusMessageType.RESOURCE_CREATED,
            {
                "resource_type": content_type,
                "title": title,
                "content": stringified_content,
                "metadata": json.dumps(metadata, indent=2),
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
            product_description (str): Description of the product.
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
            (
                StatusMessageType.STATUS,
                f"Creating copy for {copy._copy_class_name} marketing",
            )
        )

        try:
            await copy.initialize()
            for _ in range(self.num_revisions):
                await copy.improve()
        except:
            traceback.print_exc()
            return

        _submit_copy(self.feed, copy)

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
                MARKETS=json.dumps(market.model_dump()),
                DEMOGRAPHICS=json.dumps(audience.demographics),
                CHANNEL=channel.name,
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
                DEMOGRAPHICS=json.dumps(audience.demographics),
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

        class Response(BaseModel):
            markets: list[Market]

        self.feed.put_nowait(
            (
                StatusMessageType.STATUS,
                (
                    f"Identifying a candidate market for value proposition: "
                    f"{angle.value_proposition}"
                ),
            )
        )

        response = await self.search_llm.query_object(
            Response,
            VALUE_PROPOSITION=angle.value_proposition,
            USAGE_MODEL=angle.usage,
            TASK=(
                "Using available market research, suggest a suitable market where "
                "VALUE_PROPOSITION through USAGE would be useful."
            ),
        )

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
                    f"Identifying candidate audience for value proposition: "
                    f"{angle.value_proposition}"
                ),
            )
        )

        response = await self.reasoning_llm.query_object(
            Response,
            PROBLEM_STATEMENT=angle.problem_addressed,
            USAGE=angle.usage,
            TASK=(
                "Suggest a suitable target audience for the PROBLEM_STATEMENT with the "
                "USAGE model."
            ),
        )

        return [audience.audience.normalize() for audience in response.audiences]

    async def create_copy_for_angle(
        self,
        angle: ProductAngle,
    ):
        """
        Create copy for a specific product angle across various markets and audiences.

        Args:
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

    async def generate(
        self,
    ):
        """
        Generate a complete marketing campaign for a given product description.

        This function generates multiple angles for the product and creates copy for each
        angle across various markets and audiences.
        """

        # Get candidate angles for the product description
        class Response(BaseModel):
            candidates: list[ProductAngle]

        try:
            logger.info("Generating a marketing angle...")
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    "Generating candidate value proposition for the marketing campaign",
                )
            )
            response = await self.reasoning_llm.query_object(
                Response,
                PRODUCT_DESCRIPTION=self.product_description,
                TASK="List 3 suitable marketing angles given the PRODUCT_DESCRIPTION.",
            )
            self.feed.put_nowait(
                (
                    StatusMessageType.STATUS,
                    f"Generated marketing angles: {', '.join([candidate.value_proposition for candidate in response.candidates])}",
                )
            )
        except:
            traceback.print_exc()
            return

        # product_angles = response.candidates
        product_angles = response.candidates

        # Generate copy for each angle
        await asyncio.gather(
            *[self.create_copy_for_angle(x) for x in product_angles],
        )
