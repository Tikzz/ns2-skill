FROM python:3.6-alpine

RUN apk add --update alpine-sdk libffi-dev python3-dev build-base linux-headers pcre-dev openssl-dev

RUN adduser -D ns2-skill

WORKDIR /home/ns2-skill

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install uwsgi

COPY . .

RUN chown -R ns2-skill:ns2-skill ./
USER ns2-skill

EXPOSE 8100

CMD ["venv/bin/uwsgi", "--ini", "app.ini"]