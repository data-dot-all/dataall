FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=18
ARG PYTHON_VERSION=3.9
ARG NGINX_VERSION=1.24.0
ARG ENVSUBST_VERSION=v1.1.0

# Clean cache
RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean all; rm -rfv /var/cache/dnf

# Installing libraries
RUN dnf -y install shadow-utils wget
RUN dnf -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN dnf -y install nginx-$NGINX_VERSION
RUN dnf -y install python$PYTHON_VERSION
RUN dnf -y install python$PYTHON_VERSION-pip

RUN touch ~/.bashrc

COPY . ./

RUN python$PYTHON_VERSION -m pip install -r requirements.txt
RUN python$PYTHON_VERSION -m mkdocs build

RUN curl -L https://github.com/a8m/envsubst/releases/download/$ENVSUBST_VERSION/envsubst-`uname -s`-`uname -m` -o envsubst && \
    chmod +x envsubst && \
    mv envsubst /usr/local/bin
COPY ./docker/prod/nginx.config /etc/nginx/nginx.template

CMD ["/bin/sh", "-c", "envsubst < /etc/nginx/nginx.template > /etc/nginx/conf.d/default.conf"]

RUN cp -a site/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
