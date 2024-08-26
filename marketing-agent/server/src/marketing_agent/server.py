import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Literal, Optional, Union

import websockets
from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from marketing_agent.campaign import Campaign, StatusMessageType
from marketing_agent.llm.cerebras_engine import AsyncCerebrasEngine
from marketing_agent.llm.fireworks_engine import AsyncFireworksEngine
from marketing_agent.llm.groq_engine import AsyncGroqEngine
from marketing_agent.llm.perplexity_engine import AsyncPerplexityEngine
from marketing_agent.llm.together_engine import AsyncTogetherEngine
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# in memory storage for jobs and active connections
jobs: list[str] = []
active_connections: Dict[str, WebSocket] = {}


class StatusUpdateMessage(BaseModel):
    status: str
    message: Optional[str] = None


class ResourceCreatedMessage(BaseModel):
    resource_type: str
    title: str
    content: str
    metadata: Dict[str, Any]


class ErrorMessage(BaseModel):
    message: str


class WebSocketMessage(BaseModel):
    type: Literal["status_update", "resource_created", "error"]
    data: Union[StatusUpdateMessage, ResourceCreatedMessage, ErrorMessage]


class GenerateRequest(BaseModel):
    product_description: str
    revisions: int = 1
    provider: str = "cerebras"
    hallucinate: bool = True


@app.post("/generate")
async def generate_campaign(
    request: GenerateRequest, background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())
    jobs.append(job_id)

    background_tasks.add_task(run_campaign, job_id, request)

    return {"job_id": job_id}


@app.websocket("/status/{job_id}")
async def status_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    logger.info(f"Connection established for job {job_id}")
    active_connections[job_id] = websocket
    try:
        while True:
            if job_id not in jobs:
                await websocket.send_json({"type": "error", "message": "Job not found"})
                break

            # Wait for any message from the client to keep the connection alive
            await websocket.receive_text()
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"WebSocket connection closed normally for job {job_id}")
    except websockets.exceptions.ConnectionClosedError as e:
        if e.code == 1000:  # Normal closure
            logger.info(f"WebSocket connection closed normally for job {job_id}")
        else:
            logger.warning(
                f"WebSocket connection closed unexpectedly for job {job_id}: {e}"
            )
    except Exception as e:
        logger.error(f"Error in status websocket for job {job_id}: {e}")
    finally:
        del active_connections[job_id]
        if not websocket.client_state.DISCONNECTED:
            await websocket.close()


async def send_status_update(
    job_id: str,
    websocket_message: WebSocketMessage,
):
    if active_connections.get(job_id):
        logger.info(f"Sending status update for job {job_id}, {websocket_message}")
        websocket = active_connections[job_id]
        await websocket.send_json(websocket_message.model_dump())
    else:
        logger.error(f"No active connection for job {job_id}")


async def run_campaign(job_id: str, request: GenerateRequest):
    logger.info(f"Running campaign for job {job_id}")
    await send_status_update(
        job_id,
        WebSocketMessage(
            type="status_update",
            data=StatusUpdateMessage(status="running", message="Campaign started"),
        ),
    )

    # Set up LLM engines
    if request.provider == "cerebras":
        reasoning_llm = AsyncCerebrasEngine()
    elif request.provider == "fireworks":
        reasoning_llm = AsyncFireworksEngine()
    elif request.provider == "groq":
        reasoning_llm = AsyncGroqEngine()
    elif request.provider == "together":
        reasoning_llm = AsyncTogetherEngine()
    else:
        await send_status_update(
            job_id,
            WebSocketMessage(
                type="error",
                data=ErrorMessage(message=f"Unsupported provider: {request.provider}"),
            ),
        )
        return

    if request.hallucinate:
        search_llm = reasoning_llm
    else:
        search_llm = AsyncPerplexityEngine()

    # Create a queue to receive status updates and generated copy
    logger.info(f"Creating queue for job {job_id}")
    feed = asyncio.Queue()
    feed_task = asyncio.create_task(process_feed_updates(job_id, feed))

    campaign = Campaign(
        reasoning_llm, search_llm, request.product_description, request.revisions, feed
    )
    try:
        await campaign.generate()
        logger.info(f"Campaign completed for job {job_id}")
        await send_status_update(
            job_id,
            WebSocketMessage(
                type="status_update",
                data=StatusUpdateMessage(
                    status="completed", message="Campaign completed"
                ),
            ),
        )
    except Exception as e:
        logger.error(f"Error in campaign for job {job_id}: {e}")
        await send_status_update(
            job_id,
            WebSocketMessage(
                type="error",
                data=ErrorMessage(message=str(e)),
            ),
        )
    finally:
        logger.info(f"Cancelling feed task for job {job_id} if not already done...")
        feed_task.cancel()


async def process_feed_updates(job_id: str, feed: asyncio.Queue):
    while True:
        message_type, message = await feed.get()
        logger.info(
            f"Processing campaign message type: {message_type} and message: {message}"
        )
        if message_type == StatusMessageType.STATUS:
            if message == "Campaign completed":
                break

            await send_status_update(
                job_id,
                WebSocketMessage(
                    type="status_update",
                    data=StatusUpdateMessage(status="running", message=message),
                ),
            )

        elif message_type == StatusMessageType.RESOURCE_CREATED:
            await send_status_update(
                job_id,
                WebSocketMessage(
                    type="resource_created",
                    data=ResourceCreatedMessage(
                        resource_type=message["resource_type"],
                        title=message["title"],
                        content=message["content"],
                        metadata=json.loads(message["metadata"]),
                    ),
                ),
            )
