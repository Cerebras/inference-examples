import asyncio
import json
import os

import aiohttp
import websockets


async def generate_campaign(product_description, options):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/generate",
            json=options,
        ) as response:
            result = await response.json()
            return result["job_id"]


async def listen_for_updates(job_id):
    uri = f"ws://localhost:8000/status/{job_id}"
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/messages_{job_id}.json"

    async with websockets.connect(uri) as websocket:
        print("Connected to websocket")
        messages = []
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {json.dumps(data, indent=2)}")

                messages.append(data)
                with open(output_file, "w") as f:
                    json.dump(messages, f, indent=2)

                if (
                    data["type"] == "status_update"
                    and data["data"]["status"] == "completed"
                ):
                    print("Campaign generation completed.")
                    break
                elif data["type"] == "error":
                    print(f"Error occurred: {data['data']['message']}")
                    break
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break


async def main():
    # product_description = input("Enter product description: ")
    product_description = "A new product that is a combination of a laptop and a tablet"
    options = {
        "product_description": product_description,
        "revisions": 1,
        "provider": "cerebras",
        "hallucinate": True,
    }
    job_id = await generate_campaign(product_description, options)
    print(f"Campaign generation started. Job ID: {job_id}")
    await listen_for_updates(job_id)


if __name__ == "__main__":
    asyncio.run(main())
