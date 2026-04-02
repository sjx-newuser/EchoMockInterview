# Use standard Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS dependencies for compiled packages and AI libraries
# Replace Debian APT source with Aliyun mirror to speed up apt-get
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch and torchaudio (CPU version)
# Use Aliyun PyPI mirror as primary index, and PyTorch official CPU repo as extra
RUN pip install --no-cache-dir torch torchaudio \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Pre-install cffi to avoid bcrypt build failure (if bcrypt version is old)
RUN pip install --no-cache-dir cffi

# Copy and install Python requirements
COPY requirements.txt .
# Use Aliyun mirror for all packages to speed up downloads
RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://mirrors.aliyun.com/pypi/simple/

# Copy application code
COPY ./app /app/app
# Copy scripts
COPY ./scripts /app/scripts
# Copy entrypoint
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Run application
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]