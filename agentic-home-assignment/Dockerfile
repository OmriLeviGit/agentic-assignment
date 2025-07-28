# Use Python 3.11 image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install requirements
RUN pip install -r requirements.txt

# Copy your files
COPY . .

# Run your app
CMD ["python", "main.py"]