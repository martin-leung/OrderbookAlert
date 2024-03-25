# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app/AlertTool

# Copy the current directory contents into the container at /app
COPY . /app/AlertTool

# Install any needed dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application when the container launches
CMD ["python", "main.py"]
