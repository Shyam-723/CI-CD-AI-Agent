# Use an official Python runtime as a parent image, 3.10 slim version is lightweight
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies: git, curl, and gh (GitHub CLI)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our action scripts into the container
COPY scripts /app/scripts
COPY entrypoint.sh /app/entrypoint.sh

# Make sure our scripts are executable
RUN chmod +x /app/scripts/*.sh /app/entrypoint.sh /app/scripts/*.py

# Code file to execute when the docker container starts up
ENTRYPOINT ["/app/entrypoint.sh"]
