FROM python:3.9

SHELL ["/bin/bash", "-c"]

RUN echo "Creating image..."

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/
COPY health_checker.py /app/
COPY websites_cleaned.csv /app/

EXPOSE 8443

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8443"]