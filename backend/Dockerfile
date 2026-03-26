# Use miniconda as base image
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY environment.yml /tmp/environment.yml

# Create conda environment
RUN conda env create -f /tmp/environment.yml && conda clean -a

# Set work directory
WORKDIR /app

# Copy project
COPY ./app /app/app

# Run application using the conda environment
CMD ["conda", "run", "--no-capture-output", "-n", "mock-interview", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
