import asyncio
import time
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, Depends, Query
import pandas as pd
import io
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from colorama import init, Fore, Style

from src import config as app_config
from src import llm, news_fetcher, schemas

# --- App Setup ---
init(autoreset=True) # Colorama

app = FastAPI(
    title=app_config.APP_TITLE,
    description=app_config.APP_DESCRIPTION,
    version=app_config.APP_VERSION,
)
console = Console()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State and Connection Management ---
class AppState:
    def __init__(self):
        self.is_running = False
        self.background_tasks = []
        self.processed_articles = []
        self.article_queue = asyncio.Queue()

app_state = AppState()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Background Worker ---
async def article_producer(topic: str):
    """Fetches news and puts articles into the queue."""
    while app_state.is_running:
        logger.info(f"Fetching news for topic: '{topic}'")
        articles = news_fetcher.fetch_google_news(topic)
        if articles:
            for article in articles:
                # Avoid putting duplicate articles in the queue
                if article.link not in [a.link for a in app_state.processed_articles]:
                    await app_state.article_queue.put(article)
        await asyncio.sleep(60) # Fetch news every 60 seconds

async def news_worker(worker_id: int):
    logger.info(f"Worker {worker_id} started.")
    while app_state.is_running:
        try:
            article: schemas.NewsArticle = await app_state.article_queue.get()
            if not app_state.is_running: 
                app_state.article_queue.task_done()
                break

            start_time = time.time()
            logger.info(f"Worker {worker_id} processing: {article.title}")
            analysis = await llm.get_llm_analysis(article.summary)
            processing_time = time.time() - start_time

            log_panel = Panel(Text(json.dumps(analysis.model_dump(), indent=4)),
                                title=f"{Fore.CYAN}Analyzed: {article.title}{Style.RESET_ALL}",
                                border_style="green")
            console.print(log_panel)
            logger.success(f"Worker {worker_id} finished processing: {article.title} in {processing_time:.2f}s")

            response = schemas.WebSocketResponse(
                task_id=f"task_{uuid.uuid4()}",
                title=article.title,
                link=article.link,
                summary=article.summary,
                published=article.published,
                analysis=analysis,
                processing_time=processing_time,
                tokens_per_second=analysis.tokens_per_second
            )
            app_state.processed_articles.append(response.model_dump())
            await manager.broadcast(response.model_dump_json())
            app_state.article_queue.task_done()

        except Exception as e:
            logger.error(f"Error in news worker: {e}")
            await asyncio.sleep(30)
    
    logger.info(f"Worker {worker_id} has stopped.")

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def get_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/clear")
async def clear_data():
    """Clears the analyzed articles list."""
    app_state.analyzed_articles.clear()
    logger.info("Cleared all analyzed articles.")
    return {"message": "Analyzed articles cleared successfully."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        status = "running" if app_state.is_running else "paused"
        await websocket.send_text(json.dumps({"status": status}))
        while True:
            await websocket.receive_text() # Keep connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")

@app.post("/start")
async def start_processing(topic: str = Query("Technology", description="News topic to track"), power_mode: bool = Query(False, description="Enable Power Mode for parallel agents")):
    if not app_state.is_running:
        app_state.is_running = True
        app_state.processed_articles = []
        while not app_state.article_queue.empty():
            app_state.article_queue.get_nowait()

        num_agents = 5 if power_mode else 1
        app_state.background_tasks = []

        # Start one producer
        producer_task = asyncio.create_task(article_producer(topic))
        app_state.background_tasks.append(producer_task)

        # Start consumers
        for i in range(num_agents):
            task = asyncio.create_task(news_worker(i + 1))
            app_state.background_tasks.append(task)
        await manager.broadcast(json.dumps({"status": "running"}))
        return {"status": "News feed started"}
    return {"status": "News feed is already running"}

@app.post("/pause")
async def pause_news_feed():
    if app_state.is_running and app_state.background_tasks:
        app_state.is_running = False
        for task in app_state.background_tasks:
            task.cancel()
        app_state.background_tasks = []
        logger.info("News processing paused.")
        await manager.broadcast(json.dumps({"status": "paused"}))
        return {"status": "paused"}
    return {"status": "not running"}


@app.get("/export/csv")
async def export_csv():
    if not app_state.processed_articles:
        return {"message": "No data to export."}

    df = pd.json_normalize(app_state.processed_articles, sep='_')
    
    # Create a string buffer to hold CSV data
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]),
                               media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=news_analysis_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    
    return response
