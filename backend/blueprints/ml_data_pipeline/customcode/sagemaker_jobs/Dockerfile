FROM public.ecr.aws/docker/library/python:3.7.12-slim-buster

ARG SCRIPT_PATH
ARG PYTHON_VERSION=3.7

RUN apt-get update -y && \
  apt-get install --no-install-recommends -y -q \
  git libpq-dev python-dev && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

COPY smjobs /opt/program

WORKDIR /opt/program

COPY smjobs/$SCRIPT_PATH train

RUN python$PYTHON_VERSION -m pip install --upgrade pip
RUN python$PYTHON_VERSION -m pip install .


ENTRYPOINT ["python3"]
