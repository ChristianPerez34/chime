FROM python:3.11-slim-bullseye
COPY . /chime
WORKDIR /chime
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt