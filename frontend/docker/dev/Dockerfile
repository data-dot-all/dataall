FROM public.ecr.aws/docker/library/node:18-slim

WORKDIR /app

COPY package.json ./
COPY yarn.lock ./

RUN yarn install

COPY ./docker/dev/.env .
COPY . .

# Disable linting before starting the server
ENV DISABLE_ESLINT_PLUGIN=true

# Set the port to serve the application
ENV PORT=80

CMD yarn start
