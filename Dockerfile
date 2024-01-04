# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install additional dependencies for wxPython
RUN apt-get update && apt-get install -y build-essential libgtk-3-dev
RUN pip install --upgrade pip

RUN pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-9 wxPython

# RUN pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the local wxPython app source code into the container
COPY . .

# Set the display environment variable for GUI support
ENV DISPLAY=:0

# Run the wxPython GUI app
CMD ["python", "devsimpy.py"]