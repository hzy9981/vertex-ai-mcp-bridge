# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy the current directory contents into the container at /app
COPY . /app

# Install the project and its dependencies using uv
RUN uv pip install --system .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the server when the container launches
CMD ["python", "-m", "vertex.server", "--transport=sse"]
