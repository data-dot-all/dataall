FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG FUNCTION_DIR="/home/app/"
# setting a default but should be overridden by the build command
ARG PYTHON_VERSION=python3.12
ENV PYTHON_VERSION=${PYTHON_VERSION}
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser
ARG CONTAINER_UID=999

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
RUN dnf install -y ${PYTHON_VERSION}
RUN dnf -y install ${PYTHON_VERSION}-pip ${PYTHON_VERSION}-devel

## Add container user group
RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -u ${CONTAINER_UID} -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local
RUN chown -R ${CONTAINER_USER}:root /tmp

## Add your source
WORKDIR ${FUNCTION_DIR}
RUN chown -R ${CONTAINER_USER}:root ${FUNCTION_DIR}

USER ${CONTAINER_USER}

# App specific requirements
COPY --chown=${CONTAINER_USER}:root backend/requirements.txt ./requirements.txt

# Install App requirements
RUN ${PYTHON_VERSION} -m pip install setuptools --prefix=/usr/local
RUN ${PYTHON_VERSION} -m pip install -r requirements.txt --prefix=/usr/local

# App code
COPY --chown=${CONTAINER_USER}:root backend/. ./

# App configuration file
ENV config_location="config.json"
COPY --chown=${CONTAINER_USER}:root config.json ./config.json

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN ${PYTHON_VERSION} -m pip install awslambdaric --target ${FUNCTION_DIR}

COPY --chmod=755 <<EOT /awslambdaric.sh
#!/usr/bin/env bash
${PYTHON_VERSION} -m awslambdaric \$@
EOT

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "/awslambdaric.sh" ]
CMD ["auth_handler.handler"]
