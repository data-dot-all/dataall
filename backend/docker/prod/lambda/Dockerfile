FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG FUNCTION_DIR="/home/app/"
ARG PYTHON_VERSION=python3.8

RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean packages; dnf clean headers; dnf clean metadata; dnf clean all; rm -rfv /var/cache/dnf

RUN dnf -y install shadow-utils wget
RUN dnf -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN dnf install $PYTHON_VERSION
RUN dnf -y install python38-devel

## Add your source
WORKDIR ${FUNCTION_DIR}

COPY backend/requirements.txt ./requirements.txt
RUN $PYTHON_VERSION -m pip install -U pip
RUN $PYTHON_VERSION -m pip install -r requirements.txt -t .

COPY backend/. ./

ENV config_location="config.json"
COPY config.json ./config.json

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN $PYTHON_VERSION -m pip install awslambdaric --target ${FUNCTION_DIR}

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "python3.8", "-m", "awslambdaric" ]
CMD ["auth_handler.handler"]
