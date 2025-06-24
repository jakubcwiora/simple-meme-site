# Use official Python image
FROM python:3.14.0b3-alpine3.21

# Set working directory inside container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose port 5000 (Flask default)
EXPOSE 5000

# Only define non-sensitive environment variables
ENV DB_HOST="" \
    DB_USER="" \
    DB_NAME=""


# Run the Flask app
CMD ["python", "main.py"]