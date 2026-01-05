# HACI Quick Start Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose demo port
EXPOSE 8080

# Run the web demo server
CMD ["python", "web_demo.py"]
