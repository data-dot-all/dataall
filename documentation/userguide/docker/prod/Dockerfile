FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=18
ARG PYTHON_VERSION=3.8
ARG NGINX_VERSION=1.12
ARG ENVSUBST_VERSION=v1.1.0

RUN dnf -y install shadow-utils wget
RUN dnf -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN dnf install python$PYTHON_VERSION
RUN dnf install nginx$NGINX_VERSION

RUN touch ~/.bashrc

COPY . ./

RUN python$PYTHON_VERSION -m pip install -U pip
RUN python$PYTHON_VERSION -m pip install -r requirements.txt
RUN python$PYTHON_VERSION -m mkdocs build


RUN curl -L https://github.com/a8m/envsubst/releases/download/$ENVSUBST_VERSION/envsubst-`uname -s`-`uname -m` -o envsubst && \
    chmod +x envsubst && \
    mv envsubst /usr/local/bin
COPY ./docker/prod/nginx.config /etc/nginx/nginx.template

CMD ["/bin/sh", "-c", "envsubst < /etc/nginx/nginx.template > /etc/nginx/conf.d/default.conf"]

RUN cp -a site/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
