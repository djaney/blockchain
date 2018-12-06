FROM python:3-alpine
ENV FLASK_APP=web.py
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

ENTRYPOINT flask run -h 0.0.0.0
