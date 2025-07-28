FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main processing script
COPY process_pdf.py /app/

# Make sure the script is executable
RUN chmod +x /app/process_pdf.py

# Set the entrypoint for batch processing
ENTRYPOINT ["python", "process_pdf.py"]
