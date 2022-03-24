FROM public.ecr.aws/amazonlinux/amazonlinux:latest

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

RUN . ~/.nvm/nvm.sh && npm install -g npm yarn

COPY package.json yarn.lock ./

RUN . ~/.nvm/nvm.sh && yarn install

ENV PATH="./node_modules/.bin:$PATH"

COPY ./docker/dev/.env ./

COPY ./docker/dev/nginx.config /etc/nginx/nginx.template

RUN cp /etc/nginx/nginx.template /etc/nginx/conf.d/default.conf

COPY . ./

RUN . ~/.nvm/nvm.sh && yarn build

RUN cp -a build/. /usr/share/nginx/html/

CMD ["nginx", "-g", "daemon off;"]
