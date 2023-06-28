FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG NODE_VERSION=16
ARG NGINX_VERSION=1.12
ARG NVM_VERSION=v0.37.0

RUN yum update -y && \
    yum install -y tar gzip openssl && \
    yum clean all -y
RUN amazon-linux-extras install nginx$NGINX_VERSION

RUN touch ~/.bashrc

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh | bash
RUN . ~/.nvm/nvm.sh && nvm install node
RUN echo '. ~/.nvm/nvm.sh' >>  ~/.bashrc

COPY package.json package-lock.json ./

RUN . ~/.nvm/nvm.sh && npm install && npm clean cache --force

ENV PATH="./node_modules/.bin:$PATH"

COPY ./docker/dev/.env ./

COPY ./docker/dev/nginx.config /etc/nginx/nginx.template

RUN cp /etc/nginx/nginx.template /etc/nginx/nginx.conf

COPY . ./

RUN . ~/.nvm/nvm.sh && npm build

RUN cp -a build/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
