FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG FUNCTION_DIR="/home/app/"
ARG PYTHON_VERSION=python3.8

RUN yum upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    yum autoremove -y; \
    yum clean packages; yum clean headers; yum clean metadata; yum clean all; rm -rfv /var/cache/yum

RUN yum -y install shadow-utils wget
RUN yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN amazon-linux-extras install $PYTHON_VERSION
RUN yum -y install python38-devel

## Global code
WORKDIR ${FUNCTION_DIR}
COPY global/. ./
RUN $PYTHON_VERSION -m pip install -U pip
RUN $PYTHON_VERSION -m pip install -r tools/backend/requirements.txt -t .


# Module code
COPY ${MODULE_PATH}/backend/api/. ./core/backend/api/
COPY ${MODULE_PATH}/backend/db/models/. ./core/backend/db/models/
COPY ${MODULE_PATH}/backend/db/operations/. ./core/backend/db/operations/

## You must add the Lambda Runtime Interface Client (RIC) for your runtime.
RUN $PYTHON_VERSION -m pip install awslambdaric --target ${FUNCTION_DIR}

# Command can be overwritten by providing a different command in the template directly.
ENTRYPOINT [ "python3.8", "-m", "awslambdaric" ]
CMD ["auth_handler.handler"]
