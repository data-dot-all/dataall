FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG FUNCTION_DIR="/home/app/"
ARG PYTHON_VERSION=python3.9
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser


# Clean cache
RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean all; rm -rfv /var/cache/dnf

# Install libraries
RUN dnf -y install \
    shadow-utils wget openssl-devel bzip2-devel libffi-devel \
    postgresql-devel gcc unzip tar gzip

# Install Python
RUN dnf install $PYTHON_VERSION
RUN dnf -y install python3-pip python3-devel

## Add container user group
RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local
RUN chown -R ${CONTAINER_USER}:root /tmp

## Add your source
WORKDIR ${FUNCTION_DIR}
RUN chown -R ${CONTAINER_USER}:root ${FUNCTION_DIR}

USER ${CONTAINER_USER}

# App specific requirements
COPY --chown=${CONTAINER_USER}:root backend/requirements.txt ./requirements.txt

# Install App requirements
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install setuptools --prefix=/usr/local"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r requirements.txt --prefix=/usr/local"

# App code
COPY --chown=${CONTAINER_USER}:root backend/. ./

# App configuration file
ENV config_location="config.json"
COPY --chown=${CONTAINER_USER}:root config.json ./config.json

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN $PYTHON_VERSION -m pip install awslambdaric --target ${FUNCTION_DIR}

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "python3.9", "-m", "awslambdaric" ]
CMD ["auth_handler.handler"]
