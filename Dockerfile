
FROM python:3.12

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
