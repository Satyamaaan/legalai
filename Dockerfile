FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_APP=app.main:create_app \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    UPLOAD_FOLDER=/tmp/uploads \
    TEMP_PDF_DIR=/tmp/pdfs \
    TESSERACT_PATH=/usr/bin/tesseract

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing dependencies
    poppler-utils \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-guj \
    # WeasyPrint dependencies
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    fonts-freefont-ttf \
    fonts-liberation \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Create directories with correct permissions
    && mkdir -p /app /tmp/uploads /tmp/pdfs /logs \
    && chown -R appuser:appuser /app /tmp/uploads /tmp/pdfs /logs

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . /app/

# Switch to non-root user
USER appuser

# Create directories for temporary files
RUN mkdir -p ${UPLOAD_FOLDER} ${TEMP_PDF_DIR}

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app.main:app"]
