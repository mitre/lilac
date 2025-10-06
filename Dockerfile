# (C) 2025 The MITRE Corporation. All Rights Reserved.

# Use the official Python 3.10 image as the base image
FROM python:3.10.17-slim

# Set the working directory inside the container
WORKDIR /app

RUN apt-get -y update
RUN apt-get -y install curl
# Copy the requirements.txt file into the container
COPY requirements-linux.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container
COPY demo.py .
COPY ./assets ./assets
COPY ./models ./models
COPY ./prompt_templates ./prompt_templates
COPY metrics.py .

# Expose the port your app will run on
EXPOSE ${PORT}



# Command to run your Python app
#CMD ["panel", "serve", "demo.py", "--autoreload", "--static-dirs", "assets=./assets", "--port", "4200", "--address", "0.0.0.0", "--allow-websocket-origin", "jbui-dev.mitre.org:4200"]
