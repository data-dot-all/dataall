FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=18
ARG PYTHON_VERSION=3.9
ARG NGINX_VERSION=1.24.0
ARG NGINX_VERSION=1.24.0
ARG ENVSUBST_VERSION=v1.1.0
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser

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

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -r -m -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}

RUN mkdir -p /var/cache/nginx /var/log/nginx /var/lib/nginx /var/run/nginx /var/www/html && \
    chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /var/cache/nginx /var/log/nginx /var/lib/nginx /var/run/nginx /var/www/html && \
    touch /run/nginx.pid && chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /run/nginx.pid && \
    mkdir -p /etc/nginx/templates /etc/nginx/ssl/certs && \
    chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /etc/nginx

# Install necessary packages and grant permissions
RUN setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx

WORKDIR /app

RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /usr/local/
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /tmp
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /usr/share/nginx
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /etc/nginx
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /app

USER ${CONTAINER_USER}

RUN touch ~/.bashrc

COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} . ./

RUN python$PYTHON_VERSION -m pip install -r ./requirements.txt
RUN python$PYTHON_VERSION -m mkdocs build -d usr/local/site

RUN curl -L https://github.com/a8m/envsubst/releases/download/$ENVSUBST_VERSION/envsubst-`uname -s`-`uname -m` -o /usr/local/bin/envsubst && \
    chmod +x /usr/local/bin/envsubst
COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./docker/prod/nginx.config /etc/nginx/nginx.template

CMD ["/bin/sh", "-c", "/usr/local/bin/envsubst < /etc/nginx/nginx.template > /etc/nginx/conf.d/default.conf"]

RUN cp -a usr/local/site/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
