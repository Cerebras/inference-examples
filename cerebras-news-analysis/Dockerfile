# --- Stage 1: Build Stage ---
# Use an official Python image as a parent image. The 'slim' variant is smaller.
FROM python:3.11-slim AS builder

# Set the working directory in the container.
WORKDIR /app

# Install uv, the fast package manager.
RUN pip install uv

# Copy dependency definition files.
COPY pyproject.toml uv.lock* ./

# Install dependencies into a virtual environment using uv.
# This creates a self-contained environment and leverages caching.
RUN uv venv /app/venv && \
    . /app/venv/bin/activate && \
    uv pip install --no-cache-dir -r pyproject.toml

# Copy the application source code.
COPY backend/ ./backend/

# Install the application itself into the venv.
RUN . /app/venv/bin/activate && uv pip install --no-cache-dir .

# --- Stage 2: Final Stage ---
# Use a lean base image for the final production container.
FROM python:3.11-slim

# Set the working directory.
WORKDIR /app

# Copy the virtual environment from the builder stage.
COPY --from=builder /app/venv ./venv

# Copy the application code.
COPY backend/ ./backend/

# Activate the virtual environment by adding its bin to the PATH.
ENV PATH="/app/venv/bin:$PATH"

# Expose the port the app runs on.
EXPOSE 8000

# Define the command to run the application.
# The server is started with uvicorn, listening on all interfaces (0.0.0.0).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
