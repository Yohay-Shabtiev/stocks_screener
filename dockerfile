# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system deps (optional but often useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first (for better Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project

COPY src/main.py ./src/
COPY src/lists.py ./src/
# options package: only __init__.py and iv_module.py
COPY src/options/__init__.py src/options/iv_module.py ./src/options/

# indicators package: only __init__.py and data_fetch.py
COPY src/indicators/__init__.py src/indicators/data_fetch.py src/indicators/indicators.py ./src/indicators/

# Default command: run your main script
CMD ["python", "src/main.py"]
