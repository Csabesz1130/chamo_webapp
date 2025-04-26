FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
COPY ap_analyzer /app/ap_analyzer
CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
