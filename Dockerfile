# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch and Torchaudio for CPU
RUN pip install torch torchaudio -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install DeepFilterNet
RUN pip install deepfilternet
RUN pip install Flask


# Uncomment the following line to include data loading functionality for training (Linux only)
# RUN pip install 'deepfilternet[train]'

# Copy the application code to the container
COPY . .

# Command to run the application (replace 'app.py' with your script name)
CMD ["python", "app.py"]
