FROM python:3.9.6-buster

# Configure the locale
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY requirements.txt /
RUN pip install -r requirements.txt

ADD . /relfinder
WORKDIR /relfinder

EXPOSE 5000

ENV PYTHONUNBUFFERED 1

CMD gunicorn --worker-class gevent --bind 0.0.0.0:5000 api:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info