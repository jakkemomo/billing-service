FROM python:slim

WORKDIR /usr/src/billing_api

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/usr/src:${PYTHONPATH}"

RUN apt-get update && apt-get install libssl-dev -y python3-dev gcc && pip3 install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
