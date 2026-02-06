FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy streamlit files
COPY velov_dashboard_docker.py .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the streamlit
CMD ["streamlit", "run", "velov_dashboard_docker.py", "--server.port=8501", "--server.address=0.0.0.0"]
