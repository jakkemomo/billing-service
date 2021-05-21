FROM python:3.8.3-alpine

WORKDIR /usr/src/admin_panel

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/usr/src:${PYTHONPATH}"

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip3 install --upgrade pip
COPY . .
RUN pip3 install -r requirements.txt

ENTRYPOINT ["sh", "entrypoint.sh"]
