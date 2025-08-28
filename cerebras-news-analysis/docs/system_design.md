# System Design

This document outlines the system architecture for the Real-Time News Analysis application. The system is designed to be a scalable, high-performance pipeline for fetching, analyzing, and displaying news insights.

## Core Components

- **FastAPI Backend**: Serves as the central hub of the application, handling API requests, managing background tasks, and serving the frontend UI.
- **News Fetcher**: A dedicated module (`news_fetcher.py`) responsible for fetching the latest news articles from Google News.
- **Cerebras Inference**: The core analysis engine, leveraging a large language model for rapid sentiment analysis, topic extraction, and summarization.
- **HTML/Jinja2 Frontend**: A lightweight, single-page web interface for displaying the analysis results in real time.
- **WebSockets**: Enables real-time communication between the backend and frontend, allowing for live updates as new articles are processed.

## Data Flow

1.  The application starts, and the user initiates the news feed from the web UI.
2.  A background task is triggered in the FastAPI backend, which continuously fetches news articles using the `News Fetcher`.
3.  Each new article is placed into a queue for processing.
4.  Worker tasks pick up articles from the queue and send them to the Cerebras Inference API for analysis.
5.  The analysis results are received and broadcasted to the frontend via WebSockets.
6.  The frontend UI dynamically updates to display the latest insights.

## Scalability

The system is designed with scalability in mind:

- **Horizontal Scaling**: The application can be deployed across multiple instances to handle increased load.
- **Asynchronous Processing**: The use of `asyncio` and background tasks allows for non-blocking I/O and efficient resource utilization.
- **Containerization**: Docker support ensures consistent and reproducible deployments in various environments.
