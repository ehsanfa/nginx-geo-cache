FROM python:3.9-alpine

WORKDIR /app

COPY deploy/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY src /app

ENV FLASK_ENV=development
ENV FLASK_APP=index.py

CMD python -m flask run --host 0.0.0.0 --port 80