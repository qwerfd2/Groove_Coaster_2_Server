FROM python:3.9
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip --no-cache-dir
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./api/
COPY 7002.py ./
CMD ["python", "/app/7002.py"]