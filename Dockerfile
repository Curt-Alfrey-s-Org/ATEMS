FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port 5000
EXPOSE 5000

# Run gunicorn with config
CMD ["gunicorn", "-c", "gunicorn.conf.py", "atems:create_app()"]
