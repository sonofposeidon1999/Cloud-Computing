FROM python:3.7-slim-stretch
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir -p /code
RUN python -m pip install -U pip
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
COPY . /code
WORKDIR /code
