# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else (including your templates folder)
COPY . .

# Expose the port FastAPI uses
EXPOSE 8000

# Start command for root-level main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]