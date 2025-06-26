FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# This copies the 'app' directory, pyproject.toml, etc.
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.main
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port 5000 for the Flask application
EXPOSE 5000

# Run the Flask application
# Using 'flask run' is convenient for development, but for production,
# a WSGI server like Gunicorn is recommended.
CMD ["flask", "run"]

# To use Gunicorn (recommended for production):
# 1. Add gunicorn to your requirements.txt
# 2. Uncomment the following line and comment out the 'CMD ["flask", "run"]' line
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]
