# LLM Real-Time News Analysis

This project provides a real-time news analysis pipeline that leverages the high-speed inference capabilities of Cerebras AI. It fetches the latest news from Google News, performs rapid analysis to extract key insights, and presents them through a dynamic, single-page web interface built with FastAPI and HTML/Jinja2 templates.

![Real-Time News Analysis in Action](docs/images/cerebras_realtime_analysis.gif)

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#1-installation)
  - [Environment Setup](#2-environment-setup)
  - [Running the Application](#3-running-the-application)
- [Docker Deployment](#4-docker-deployment-optional)
- [Documentation](#documentation)

## Features

- **Real-Time News Fetching**: Gathers the latest news articles from Google News.
- **High-Speed LLM Analysis**: Utilizes Cerebras' inference service for rapid analysis of sentiment, key topics, and summaries.
- **Dynamic Web UI**: A responsive, single-page interface built with FastAPI and HTML/Jinja2, featuring real-time updates via WebSockets.
- **RESTful API**: The FastAPI backend exposes endpoints for controlling the news feed and streaming analysis results.
- **Containerized Deployment**: Docker support for easy and consistent deployment.

## Project Structure

```
.
├── backend/
│   ├── src/
│   │   ├── config.py
│   │   ├── llm.py
│   │   ├── news_fetcher.py
│   │   ├── prompts.py
│   │   └── schemas.py
│   ├── templates/
│   │   └── index.html
│   ├── cli.py
│   └── main.py
├── docs/
│   └── images/
│       └── cerebras_realtime_analysis.gif
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── justfile
├── pyproject.toml
└── uv.lock
```

## Quick Start

### Prerequisites

- Python 3.9+
- `uv` package manager (`pip install uv`)
- Docker (optional, for containerized deployment)

### 1. Installation

Clone the repository and install the dependencies using `uv`:

```bash
git clone https://github.com/seduerr91/inference-examples
cd llm-realtime-news-analysis
uv pip install -e .
```

### 2. Environment Setup

Copy the example `.env.example` file to `.env` and add your `CEREBRAS_API_KEY`.

```bash
cp .env.example .env
# Now, edit .env with your key
```

### 3. Running the Application

Start the application with a single command:

```bash
just run
```

Navigate to `http://localhost:8000` to view the application.

## 4. Docker Deployment (Optional)

Build and run the application using Docker:

```bash
just build-docker
just run-docker
```

## Documentation

For more detailed information about the project, please see the following documents:

- **[System Design](docs/system_design.md)**: An in-depth look at the application's architecture and data flow.
- **[Blog Post](docs/blog.md)**: A high-level overview of the project, its purpose, and its key benefits.
