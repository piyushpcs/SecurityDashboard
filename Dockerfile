# Use Python 3.9 Slim (Lightweight Linux)
FROM python:3.9-slim

# Set environment variables to make Python output logs immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install System Dependencies
# We need 'cmake' and 'build-essential' for dlib (face recognition)
# We need 'libgl1...' for OpenCV
# We need 'libasound2-dev' for simpleaudio
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to cache the installation layer)
COPY requirements.txt /app/

# Install Python Libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /app/

# Open port 8000
EXPOSE 8000

# Run the Django Server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]