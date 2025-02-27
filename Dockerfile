# Use an official Python image as a base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install environment variables from .env file
COPY .env /app/.env

# Run the script
CMD ["python", "cloudflare.py"]

