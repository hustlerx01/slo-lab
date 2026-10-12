FROM python:3.12-slim
RUN useradd -r -u 10001 app
WORKDIR /app
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py loadgen.py ./
USER 10001
EXPOSE 8000
CMD ["python", "app.py"]
