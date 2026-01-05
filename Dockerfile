FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask kubernetes
EXPOSE 5000
CMD ["python3", "api.py"]