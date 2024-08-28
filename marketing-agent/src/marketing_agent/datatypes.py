from abc import ABC, abstractmethod
from typing import List, Literal, Union

from pydantic import BaseModel, Field

from .copy_plugins import globals

# Enums

# Using a dynamic tuple to define Literal values is technically illegal, but:
#   1. Using a Literal results in more consistent behavior from the LLM
#      compared to enums,
#   2. The interpreter will allow it, even though the IDE will complain, and
#   3. This makes it much easier to make modifications to the copy types.
CopyFormat = Literal[tuple(globals.copy_plugins)]


# Pydantic Models
class ProductAngle(BaseModel):
    problem_addressed: str
    value_proposition: str
    usage: str = Field(
        ...,
        description=(
            "How does someone use the product? Web interface, API, "
            "consulting services, or anything else."
        ),
    )


class Market(BaseModel):
    market_description: str
    example_products: List[str]
    capturable_market_size_dollars: str
    market_growth_yoy: str


class Channel(BaseModel):
    name: str
    description: str
    copy_format: Union[CopyFormat, str]
    pros: List[str]
    cons: List[str]


class CopyStrategy(BaseModel):
    strategy: str
    product_positioning: str
    competitive_claim: str
    review_criteria: list[str]


class Audience(BaseModel):
    description: str
    profile: str
    profile_name: str
    decision_maker: str
    demographics: list[str]


class AudienceBase(BaseModel, ABC):
    @abstractmethod
    def normalize(self) -> Audience:
        raise NotImplementedError


class EndUserAudience(AudienceBase):
    description: str
    user_profile: str
    profile_name: str
    demographics: list[str] = Field(
        ..., description="Anything that would help target the right individuals."
    )

    def normalize(self):
        return Audience(
            description=self.description,
            profile=self.user_profile,
            profile_name=self.profile_name,
            decision_maker=self.profile_name,
            demographics=self.demographics,
        )


class EnterpriseAudience(AudienceBase):
    description: str
    enterprise_profile: str
    profile_name: str
    decision_maker: str = Field(
        ...,
        description=(
            "The role or team that would make the decision to purchase the " "product."
        ),
    )
    demographics: list[str] = Field(
        ..., description="Anything that would help target the right individuals."
    )

    def normalize(self):
        return Audience(
            description=self.description,
            profile=self.enterprise_profile,
            profile_name=self.profile_name,
            decision_maker=self.decision_maker,
            demographics=self.demographics,
        )


class GovernmentAudience(AudienceBase):
    description: str
    agency_profile: str
    profile_name: str
    decision_maker: str = Field(
        ...,
        description="The role that would make the decision to purchase the product.",
    )
    demographics: list[str] = Field(
        ..., description="Anything that would help target the right individuals."
    )

    def normalize(self):
        return Audience(
            description=self.description,
            profile=self.agency_profile,
            profile_name=self.profile_name,
            decision_maker=self.decision_maker,
            demographics=self.demographics,
        )


class AudienceUnion(BaseModel):
    type: Literal["EndUser", "Enterprise", "Government"]
    audience: Union[EndUserAudience, EnterpriseAudience, GovernmentAudience]

    def normalize(self):
        return self.audience.normalize()
