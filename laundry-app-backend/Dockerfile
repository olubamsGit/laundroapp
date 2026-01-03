FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Update pip
RUN pip install --upgrade pip

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from laundry-app-backend into /app
COPY . .

# Use Render's default port 10000
ENV PORT=8000
EXPOSE 8000

# Point to app.main because main.py is inside the app/ folder
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
