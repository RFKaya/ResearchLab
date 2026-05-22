# Mock Auth API for Shadow MFA Fatigue Lab
FROM python:3.10-slim

WORKDIR /app

# Install Flask
RUN pip install Flask

# Copy the API script
COPY mock_auth_api.py /app/mock_auth_api.py

# Expose backend port
EXPOSE 8080

CMD ["python", "mock_auth_api.py"]
