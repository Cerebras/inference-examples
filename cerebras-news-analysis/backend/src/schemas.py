from typing import List, Dict, Literal
from pydantic import BaseModel, Field

class NewsAnalysis(BaseModel):
    """
    Defines the structure for the LLM's investor-focused analysis output.
    """
    sentiment: Literal['Bullish', 'Bearish', 'Neutral'] = Field(
        ...,
        description="Overall sentiment for an investor: Bullish, Bearish, or Neutral."
    )
    confidence: float = Field(
        ...,
        description="Confidence score in the analysis, from 0.0 to 1.0.",
        ge=0.0, 
        le=1.0
    )
    affected_entities: List[str] = Field(
        ...,
        description="List of companies, stock tickers, indexes, or sectors mentioned."
    )
    impact_direction: Dict[str, Literal['Positive', 'Negative', 'Neutral']] = Field(
        ...,
        description="Dictionary mapping each entity to its expected impact direction."
    )
    magnitude: Dict[str, Literal['Low', 'Medium', 'High']] = Field(
        ...,
        description="Dictionary mapping each entity to the magnitude of the expected impact."
    )
    key_indicators: List[str] = Field(
        ...,
        description="List of key performance indicators or financial metrics mentioned (e.g., EPS, revenue growth, stock price movements)."
    )
    risks: List[str] = Field(
        ...,
        description="List of potential risks or concerns identified in the article (e.g., 'valuation risk', 'regulatory pressure')."
    )
    opportunities: List[str] = Field(
        ...,
        description="List of potential opportunities identified (e.g., 'AI growth', 'new product launch')."
    )
    time_horizon: Literal['Short-term', 'Medium-term', 'Long-term'] = Field(
        ...,
        description="The relevant time horizon for the article's impact."
    )
    sector_context: Dict[str, Literal['Bullish', 'Bearish', 'Neutral']] = Field(
        ...,
        description="Dictionary mapping mentioned sectors to their overall sentiment."
    )
    summary_explanation: str = Field(
        ...,
        description="A concise, fact-based summary for an investor, explaining the key takeaways."
    )
    tokens_per_second: float | None = Field(
        None,
        description="Inference speed in tokens per second."
    )

class WebSocketResponse(BaseModel):
    """
    Defines the structure for the data sent over the WebSocket.
    """
    task_id: str
    title: str
    link: str
    summary: str
    published: str
    analysis: NewsAnalysis
    processing_time: float
    tokens_per_second: float | None = None
