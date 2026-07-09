# Use official slim Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY trend_web_app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY trend_web_app/main.py .
COPY trend_web_app/static/ ./static/

COPY trend_web_app/naver_datalab_client.py .
COPY trend_web_app/daily_food_data/ ./daily_food_data/


# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Run uvicorn server when the container launches
CMD ["python", "main.py"]
