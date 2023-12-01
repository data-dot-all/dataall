FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG FUNCTION_DIR="/home/app/"
ARG PYTHON_VERSION=python3.9

# Clean cache
RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean all; rm -rfv /var/cache/dnf

# Install libraries
RUN dnf -y install -y \
    shadow-utils wget openssl-devel bzip2-devel libffi-devel \
    postgresql-devel gcc unzip tar gzip

# Install Python
RUN dnf install $PYTHON_VERSION
RUN dnf -y install python3-pip python3-devel

## Add source
WORKDIR ${FUNCTION_DIR}

# App specific requirements
COPY backend/requirements.txt ./requirements.txt

# Install App requirements
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install setuptools"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r requirements.txt"

# App code
COPY backend/. ./

# App configuration file
ENV config_location="config.json"
COPY config.json ./config.json

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN $PYTHON_VERSION -m pip install awslambdaric --target ${FUNCTION_DIR}

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "python3.9", "-m", "awslambdaric" ]
CMD ["auth_handler.handler"]
