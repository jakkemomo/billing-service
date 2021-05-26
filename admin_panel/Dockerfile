FROM python:3.8.3-alpine

WORKDIR /usr/src/admin_panel

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/usr/src:${PYTHONPATH}"

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev && pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

ENTRYPOINT ["sh", "entrypoint.sh"]
