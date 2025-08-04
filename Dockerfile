# Use the latest official Python image
FROM python:3.13

# Set working directory inside the container
WORKDIR /app

# Copy required files into the container
COPY requirements.txt .
COPY migrate.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run the migration script
CMD ["python", "migrate.py"]

