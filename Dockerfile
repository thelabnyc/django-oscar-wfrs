FROM python:3.9

RUN mkdir /code
WORKDIR /code

RUN apt-get update && \
    apt-get install -y gettext && \
    rm -rf /var/lib/apt/lists/*

ADD . /code/
RUN pip install -e .[development,kms]

RUN mkdir /tox
ENV TOX_WORK_DIR='/tox'
