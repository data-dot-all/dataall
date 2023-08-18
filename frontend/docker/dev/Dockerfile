FROM public.ecr.aws/docker/library/node:18-slim

WORKDIR /app

COPY ./frontend/package.json ./
COPY ./frontend/yarn.lock ./

# Install packages, use --ignore-scripts to not call postinstall, as it causes this step to fail because config.json
# is not copied yet, and copying it here will trigger new install if config changes, which is inconvenient for development.
RUN yarn install --ignore-scripts

COPY ./frontend/docker/dev/.env .
COPY ./frontend .

# Copy config.json to docker root, because app scripts read it from ".."
COPY ./config.json /

# Disable linting before starting the server
ENV DISABLE_ESLINT_PLUGIN=true

# Set the port to serve the application
ENV PORT=80

CMD yarn start
