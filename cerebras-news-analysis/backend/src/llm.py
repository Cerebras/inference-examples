import asyncio
import json
import time
from openai import AsyncOpenAI
from loguru import logger

from . import config, prompts, schemas

# Initialize the async OpenAI client
client = AsyncOpenAI(
    api_key=config.CEREBRAS_API_KEY,
    base_url=config.CEREBRAS_API_BASE,
)

async def get_llm_analysis(content: str) -> schemas.NewsAnalysis:
    """Analyzes text using the Cerebras model with native structured output."""
    try:
        news_schema = schemas.NewsAnalysis.model_json_schema()

        start_time = time.time()
        completion = await client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": prompts.SYSTEM_PROMPT},
                {"role": "user", "content": prompts.get_user_prompt(content)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "news_analysis",
                    "schema": news_schema
                }
            },
            max_tokens=2048,
            temperature=config.TEMPERATURE,
        )
        end_time = time.time()

        api_call_time = end_time - start_time
        response_content = completion.choices[0].message.content
        parsed_json = json.loads(response_content)
        analysis_obj = schemas.NewsAnalysis.model_validate(parsed_json)

        if completion.usage and completion.usage.completion_tokens and api_call_time > 0:
            tokens_per_second = completion.usage.completion_tokens / api_call_time
            analysis_obj.tokens_per_second = round(tokens_per_second, 2)

        return analysis_obj

    except Exception as e:
        logger.error(f"Error calling Cerebras API or parsing response: {e}")
        # Return a default analysis object that matches the news schema
        return schemas.NewsAnalysis(
            sentiment="Neutral",
            confidence=0.0,
            affected_entities=[],
            impact_direction={},
            magnitude={},
            key_indicators=[],
            risks=["Analysis failed due to API or parsing error."],
            opportunities=[],
            time_horizon="Short-term",
            sector_context={},
            summary_explanation=f"Could not perform analysis due to an error: {e}"
        )

if __name__ == '__main__':
    async def main():
        logger.info("Running LLM analysis in standalone test mode...")
        test_content = """
        Nvidia's stock surged to a new record high on Wednesday, as investors eagerly awaited the chipmaker's quarterly earnings report.
        The company, a key player in the AI boom, is expected to post strong results, but some analysts worry that the sky-high expectations
        could be difficult to meet. The S&P 500 also reached a new peak, driven by optimism in the tech sector.
        """
        analysis_result = await get_llm_analysis(test_content)
        if analysis_result:
            from rich import print as rprint
            print("\n--- LLM Analysis Result ---")
            rprint(analysis_result.model_dump())
            print("---------------------------\n")
        else:
            print("Failed to get analysis.")

    asyncio.run(main())