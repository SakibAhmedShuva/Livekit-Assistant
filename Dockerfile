# Dockerfile

FROM python:3.11

WORKDIR /app

# Copy requirements.txt first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set up user permissions for security (good practice)
RUN useradd -m -u 1000 user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port our Flask app will run on
EXPOSE 7860

# The command to run the application
CMD ["python", "server.py"]