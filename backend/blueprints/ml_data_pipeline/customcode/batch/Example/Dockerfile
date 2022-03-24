FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG PYTHON_VERSION=3.8

RUN yum update -y
RUN yum install -y amazon-linux-extras wget
RUN amazon-linux-extras enable python$PYTHON_VERSION
RUN yum install -y python$PYTHON_VERSION

RUN pip$PYTHON_VERSION install pipenv
COPY Pipfile /tmp
RUN cd /tmp && pipenv lock -r > requirements.txt
RUN pip$PYTHON_VERSION install -r /tmp/requirements.txt

WORKDIR /tmp

COPY example.py /usr/local/bin/example.py

USER nobody

ENTRYPOINT ["python$PYTHON_VERSION", "/usr/local/bin/example.py"]
CMD ["DB_SECRETS", "DEST_BUCKET", "REGION"]
