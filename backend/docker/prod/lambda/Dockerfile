FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG FUNCTION_DIR="/home/app/"
ARG PYTHON_VERSION=python3.8
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser


RUN yum upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    yum autoremove -y; \
    yum clean packages; yum clean headers; yum clean metadata; yum clean all; rm -rfv /var/cache/yum

RUN yum -y install shadow-utils wget
RUN yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN amazon-linux-extras install $PYTHON_VERSION
RUN yum -y install python38-devel

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local

## Add your source
WORKDIR ${FUNCTION_DIR}
RUN chown -R ${CONTAINER_USER}:root ${FUNCTION_DIR}

USER ${CONTAINER_USER}


COPY --chown=${CONTAINER_USER}:root backend/requirements.txt ./requirements.txt
RUN $PYTHON_VERSION -m pip install -U pip
RUN $PYTHON_VERSION -m pip install -r requirements.txt -t .

COPY --chown=${CONTAINER_USER}:root backend/. ./

ENV config_location="config.json"
COPY --chown=${CONTAINER_USER}:root config.json ./config.json

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN $PYTHON_VERSION -m pip install awslambdaric --target ${FUNCTION_DIR}

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "python3.8", "-m", "awslambdaric" ]
CMD ["auth_handler.handler"]
