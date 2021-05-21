FROM python:slim

WORKDIR /usr/src/billing_api

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/usr/src:${PYTHONPATH}"

RUN apt-get update && apt-get install libssl-dev -y python3-dev gcc
RUN pip3 install --upgrade pip
COPY . .
RUN pip3 install -r requirements.txt