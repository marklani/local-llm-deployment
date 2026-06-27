FROM python:3.14-slim

WORKDIR /app

# Install system dependencies needed for sqlite/pypdf if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install python requirements
RUN pip install -r requirements.txt

# Copy source code files
COPY app.py index.html ./

EXPOSE 8000

CMD ["python", "app.py"]