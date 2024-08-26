import uvicorn
from dotenv import load_dotenv

load_dotenv(override=True)

if __name__ == "__main__":
    uvicorn.run("marketing_agent.server:app", host="0.0.0.0", port=8000, reload=True)
