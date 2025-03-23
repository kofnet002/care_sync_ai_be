# Base image with Python 3.10
FROM python:3.10-slim-buster as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    netcat \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Final stage
FROM python:3.10-slim-buster

ENV HOME=/user/src \
    APP_HOME=/usr/src/app/caresyncai \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create app user and directories
RUN groupadd --system app && \
    useradd --system --gid app --shell /bin/bash --create-home app && \
    mkdir -p $APP_HOME && \
    mkdir -p $APP_HOME/media && \
    mkdir -p $APP_HOME/staticfiles

# Set work directory
WORKDIR $APP_HOME

# Install only essential runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    libmagic-dev \
    postgresql-client \
    netcat-traditional \
    dos2unix && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from base
COPY --from=base /opt/venv /opt/venv

# Copy and prepare scripts
COPY entrypoint.sh start-celeryworker.sh start-celerybeat.sh ./
RUN dos2unix entrypoint.sh start-celeryworker.sh start-celerybeat.sh && \
    chmod +x entrypoint.sh start-celeryworker.sh start-celerybeat.sh

# Ensure the file has correct permissions and Unix-style line endings
RUN dos2unix $APP_HOME/entrypoint.sh && \
    chmod +x $APP_HOME/entrypoint.sh && \
    ls -l $APP_HOME/entrypoint.sh  # Debugging: Check permissions

RUN chmod +x /usr/src/app/caresyncai/entrypoint.sh

# Copy application
COPY . .

# Set permissions
RUN chmod -R 755 media staticfiles && \
    chown -R app:app $APP_HOME && \
    chmod +x entrypoint.sh && \
    chmod +x start-celeryworker.sh && \
    chmod +x start-celerybeat.sh

USER app

ENTRYPOINT ["./entrypoint.sh"]