FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN pip install --no-cache-dir uv && \
    uv pip install --system .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs data/photos data/checkpoints

# Copy and make migration check script executable
COPY check_db_migrations.py .
RUN chmod +x check_db_migrations.py

# Expose port
EXPOSE 8000

# Run migration check and application
CMD ["sh", "-c", "python check_db_migrations.py && python main.py"]
