FROM public.ecr.aws/amazonlinux/amazonlinux:2023


ARG REACT_APP_STAGE
ARG DOMAIN
ARG NODE_VERSION=22
ARG NGINX_VERSION=1.24.0
ARG NVM_VERSION=v0.37.2
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser



# Clean cache
RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean all; rm -rfv /var/cache/dnf

# Installing libraries
RUN dnf install -y tar gzip openssl nginx-$NGINX_VERSION

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}

RUN mkdir -p /var/cache/nginx /var/log/nginx /var/lib/nginx /var/run/nginx /var/www/html && \
    chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /var/cache/nginx /var/log/nginx /var/lib/nginx /var/run/nginx /var/www/html && \
    touch /run/nginx.pid && chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /run/nginx.pid && \
    mkdir -p /etc/nginx/templates /etc/nginx/ssl/certs && \
    chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /etc/nginx

# Install necessary packages and grant permissions
RUN setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx

WORKDIR /app

RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /usr/local
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /etc/nginx
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /usr/share/nginx
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /tmp
RUN chown -R ${CONTAINER_USER}:${CONTAINER_USER_GROUP} /app

USER ${CONTAINER_USER}

RUN touch ~/.bashrc

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh | bash
RUN . ~/.nvm/nvm.sh && nvm install node
RUN echo '. ~/.nvm/nvm.sh' >> ~/.bashrc

RUN . ~/.nvm/nvm.sh && npm install -g npm@9 yarn


COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./frontend/package.json ./frontend/yarn.lock ./
COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./config.json /
# Copy vesion.json to docker root, because app scripts read it from ".."
COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./version.json /

RUN . ~/.nvm/nvm.sh && yarn install

ENV PATH="./node_modules/.bin:$PATH"

COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./frontend/docker/prod/nginx.config /etc/nginx/nginx.template

ENV SERVERNAME=$DOMAIN

RUN echo "$SERVERNAME"

RUN sed -i 's|SERVERNAME|'$SERVERNAME'|g' /etc/nginx/nginx.template

RUN cat /etc/nginx/nginx.template

RUN cp /etc/nginx/nginx.template /etc/nginx/nginx.conf

# disable nginx user cuz running as non-root
RUN sed -i 's/user nginx;/#user nginx;/g' /etc/nginx/nginx.conf

RUN cat /etc/nginx/nginx.conf

COPY --chown=${CONTAINER_USER}:${CONTAINER_USER_GROUP} ./frontend ./

RUN . ~/.nvm/nvm.sh && yarn build

RUN cp -a build/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
