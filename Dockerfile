FROM python:3.9-slim

# Install system dependencies for NFC support
RUN apt-get update && apt-get install -y \
    libusb-1.0-0-dev \
    libpcsclite1 \
    pcscd \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 nfcuser && chown -R nfcuser:nfcuser /app
USER nfcuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]