# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV CLIENT_SECRET fc32832f05b3979fe21b4f25a874544a
ENV CLIENT_ID 230182039712.249213806771
ENV VERIFICATION_TOKEN c1BpEmuZPedxDOqTlVtKIh2B

# Run app.py when the container launches
CMD ["python3", "app.py"]
