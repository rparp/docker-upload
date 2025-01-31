# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the Flask application directory into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Set the upload folder as a volume
VOLUME /app/src/instance

# Define environment variable
# ENV FLASK_APP=test.py

# Run the Flask application when the container launches
CMD ["flask", "--app=src/app.py", "run", "--host=0.0.0.0"]