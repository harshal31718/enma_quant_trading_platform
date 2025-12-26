FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY app /app/app
CMD ["uvicorn","app.api:app","--host","0.0.0.0","--port","8000"]
