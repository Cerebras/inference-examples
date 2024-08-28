import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from marketing_agent.campaign import Campaign, StatusMessageType


async def process_status_messages(feed: asyncio.Queue, output_dir: str):
    """
    Continuously print messages from the feed queue until cancelled.

    This function prints status updates and writes generated files to disk.

    Args:
        feed (asyncio.Queue): The queue to read messages from.
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        while True:
            message_type, message = await feed.get()
            if message_type == StatusMessageType.STATUS:
                print(f"STATUS: {message}")
            elif message_type == StatusMessageType.FILE_CREATED:
                filename = message["filename"]
                content = message["content"]
                print(f"FILE_CREATED: {filename}")

                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w") as f:
                    f.write(content)
    except asyncio.CancelledError:
        pass


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process arguments for the marketing campaign generator."
    )

    # Product description file argument
    parser.add_argument(
        "product",
        help='Path to the product description file. Use a single hyphen "-" to read from standard input.',
    )

    # Output directory argument
    parser.add_argument(
        "-o",
        "--output",
        default=os.path.join(os.getcwd(), "output"),
        help="Output directory path. Default is output/ in the working directory.",
    )

    # Number of revisions argument
    parser.add_argument(
        "-r",
        "--revisions",
        type=int,
        default=1,
        choices=range(0, 100),  # Assuming a reasonable upper limit
        metavar="N",
        help="Number of revisions (integer 0 or higher). Default is 1.",
    )

    # API provider argument
    parser.add_argument(
        "-p",
        "--provider",
        choices=["cerebras", "fireworks", "groq", "together"],
        default="cerebras",
        help="API provider name for the reasoning model (cerebras, fireworks, groq, or together).",
    )

    # Model name argument
    parser.add_argument(
        "-m",
        "--reasoning-model",
        default="llama3.1-70b",
        help="Provider-specific model name.",
    )

    # Perplexity model name argument
    parser.add_argument(
        "-s",
        "--search-model",
        default="llama-3.1-sonar-large-128k-online",
        help="Perplexity model name, if Perplexity search is enabled.",
    )

    # Hallucinate flag
    parser.add_argument(
        "--hallucinate",
        action="store_true",
        help="Enable hallucination mode (disable Perplexity search).",
    )

    return parser.parse_args()


async def main():
    """
    Main function to run the marketing campaign generation process.

    This function generates a marketing campaign for a product. It handles status
    messages and file creation through `process_status_messages`.
    """
    args = parse_arguments()
    if args.provider == "cerebras":
        from marketing_agent.llm.cerebras_engine import AsyncCerebrasEngine

        reasoning_llm = AsyncCerebrasEngine(args.reasoning_model)
    elif args.provider == "fireworks":
        from marketing_agent.llm.fireworks_engine import AsyncFireworksEngine

        reasoning_llm = AsyncFireworksEngine(args.reasoning_model)
    elif args.provider == "groq":
        from marketing_agent.llm.groq_engine import AsyncGroqEngine

        reasoning_llm = AsyncGroqEngine(args.reasoning_model)
    elif args.provider == "together":
        from marketing_agent.llm.together_engine import AsyncTogetherEngine

        reasoning_llm = AsyncTogetherEngine(args.reasoning_model)

    if args.hallucinate:
        search_llm = reasoning_llm
    else:
        from marketing_agent.llm.perplexity_engine import AsyncPerplexityEngine

        search_llm = AsyncPerplexityEngine(args.search_model)

    # Create a queue to receive status updates and generated copy
    feed = asyncio.Queue()
    feed_task = asyncio.create_task(process_status_messages(feed, args.output))

    # Read the product description
    if args.product == "-":
        product_description = sys.stdin.read().strip()
    else:
        with open(args.product) as f:
            product_description = f.read().strip()

    # Generate a marketing campaign for a product
    campaign = Campaign(
        reasoning_llm, search_llm, product_description, args.revisions, feed
    )
    await campaign.generate()

    # Close the queue
    feed_task.cancel()


asyncio.run(main())
