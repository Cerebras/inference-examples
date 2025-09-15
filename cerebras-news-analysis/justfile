# Test the LLM analysis
test: 
	clear
	python -m src.llm

# Run the backend service
run: 
	clear
	cd backend && python -m uvicorn main:app --reload

# Run the frontend service
fe: 
	clear
	cd frontend && streamlit run app.py

# Run the CLI
cli *args:
	clear
	python backend/cli.py {{args}}

# Clean up temporary Python files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Build the Docker image
build-docker:
	docker build -t news-analysis-backend .

# Run the Docker container
run-docker:
	docker run -p 8000:8000 --env-file .env news-analysis-backend
