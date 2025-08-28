import asyncio
import typer
import httpx
import websockets
from rich.console import Console
from rich.table import Table
import json

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

app = typer.Typer()
console = Console()

async def listen_for_news():
    """Connects to the WebSocket and prints incoming news."""
    try:
        async with websockets.connect(WS_URL) as websocket:
            console.print("[bold green]Connected to WebSocket. Waiting for news...[/bold green]")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Title", style="cyan", no_wrap=False)
                    table.add_column("Published", style="green")
                    table.add_column("Processing Time (s)", style="yellow")

                    table.add_row(
                        data['title'],
                        data['published'],
                        str(data['processing_time'])
                    )
                    
                    console.print(table)
                    console.print(f"[bold]Link:[/] [link={data['link']}]{data['link']}[/link]")
                    console.print(f"[bold]Summary:[/] {data['summary']}")
                    console.print(f"[bold]Analysis:[/] {data['analysis']}")
                    console.print("---")

                except websockets.exceptions.ConnectionClosed:
                    console.print("[bold red]WebSocket connection closed.[/bold red]")
                    break
                except Exception as e:
                    console.print(f"[bold red]An error occurred: {e}[/bold red]")
                    break
    except Exception as e:
        console.print(f"[bold red]Failed to connect to WebSocket: {e}[/bold red]")

@app.command()
def stream():
    """Connect to the WebSocket and stream news.
    """
    try:
        asyncio.run(listen_for_news())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting CLI.[/bold yellow]")

async def send_command(command: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/{command}")
            response.raise_for_status()
            console.print(f"[bold green]Successfully sent '{command}' command.[/bold green]")
            console.print(response.json())
        except httpx.RequestError as e:
            console.print(f"[bold red]Error sending '{command}' command: {e}[/bold red]")

@app.command()
def start():
    """Start the news processing."""
    asyncio.run(send_command("start"))

@app.command()
def pause():
    """Pause the news processing."""
    asyncio.run(send_command("pause"))

@app.command()
def status():
    """Get the current status of the news processing."""
    async def get_status():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{API_URL}/status")
                response.raise_for_status()
                console.print("[bold green]Current status:[/bold green]")
                console.print(response.json())
            except httpx.RequestError as e:
                console.print(f"[bold red]Error getting status: {e}[/bold red]")
    asyncio.run(get_status())

if __name__ == "__main__":
    app()
