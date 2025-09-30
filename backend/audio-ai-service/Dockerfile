# Start from a lean official Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# IMPORTANT: Install the FFmpeg system dependency
# This must be done before installing Python packages that might need it
RUN apt-get update && apt-get install -y ffmpeg

# Copy and install Python requirements first to leverage Docker's layer caching
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your application's code into the container
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# The command to run your application
# We use --host 0.0.0.0 to make the server accessible from outside the container
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]