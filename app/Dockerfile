FROM node:20 AS fe
WORKDIR /f
COPY frontend/ .
RUN npm install && npm run build
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=fe /f/dist ./static
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
