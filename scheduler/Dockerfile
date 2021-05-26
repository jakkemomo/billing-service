FROM python:slim

WORKDIR /usr/src/scheduler

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/usr/src:${PYTHONPATH}"

RUN apt-get update && apt install -y netcat
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

ENTRYPOINT ["sh", "entrypoint.sh"]
