FROM public.ecr.aws/amazonlinux/amazonlinux:2023


ARG REACT_APP_STAGE
ARG DOMAIN
ARG NODE_VERSION=18
ARG NGINX_VERSION=1.12
ARG NVM_VERSION=v0.37.0
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser


RUN dnf update -y && \
    dnf install -y tar gzip openssl && \
    dnf clean all -y
RUN dnf install nginx$NGINX_VERSION



RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}

RUN mkdir -p /var/cache/nginx && chown -R ${CONTAINER_USER}:root /var/cache/nginx && \
    mkdir -p /var/log/nginx  && chown -R ${CONTAINER_USER}:root /var/log/nginx && \
    mkdir -p /var/lib/nginx  && chown -R ${CONTAINER_USER}:root /var/lib/nginx && \
    touch /run/nginx.pid && chown -R ${CONTAINER_USER}:root /run/nginx.pid && \
    mkdir -p /etc/nginx/templates /etc/nginx/ssl/certs && \
    chown -R ${CONTAINER_USER}:root /etc/nginx



RUN chown -R ${CONTAINER_USER}:root /usr/local
RUN chown -R ${CONTAINER_USER}:root /etc/nginx
RUN chown -R ${CONTAINER_USER}:root /usr/share/nginx
RUN chown -R ${CONTAINER_USER}:root /tmp
USER ${CONTAINER_USER}


WORKDIR /app

RUN touch ~/.bashrc

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh | bash
RUN . ~/.nvm/nvm.sh && nvm install node
RUN echo '. ~/.nvm/nvm.sh' >>  ~/.bashrc

RUN . ~/.nvm/nvm.sh && npm install -g npm@9 yarn


COPY --chown=${CONTAINER_USER}:root ./frontend/package.json ./frontend/yarn.lock ./
COPY --chown=${CONTAINER_USER}:root ./config.json /

RUN . ~/.nvm/nvm.sh && yarn install

ENV PATH="./node_modules/.bin:$PATH"

COPY --chown=${CONTAINER_USER}:root ./frontend/docker/prod/nginx.config /etc/nginx/nginx.template

ENV SERVERNAME=$DOMAIN

RUN echo "$SERVERNAME"

RUN sed -i 's|SERVERNAME|'$SERVERNAME'|g' /etc/nginx/nginx.template

RUN cat /etc/nginx/nginx.template

RUN cp /etc/nginx/nginx.template /etc/nginx/nginx.conf

# disable nginx user cuz running as non-root
RUN sed -i 's/user nginx;/#user nginx;/g' /etc/nginx/nginx.conf

RUN cat /etc/nginx/nginx.conf

COPY --chown=${CONTAINER_USER}:root ./frontend ./

RUN . ~/.nvm/nvm.sh && yarn build

RUN cp -a build/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
