FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads results logs database

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]</content>
<parameter name="filePath">c:\Users\compumarts\Desktop\eea omar\Dockerfile