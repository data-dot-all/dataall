FROM public.ecr.aws/docker/library/node:18-slim

ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser

WORKDIR /app

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /app
RUN chown -R ${CONTAINER_USER}:root /tmp
USER ${CONTAINER_USER}

COPY --chown=${CONTAINER_USER}:root ./frontend/package.json ./
COPY --chown=${CONTAINER_USER}:root ./frontend/yarn.lock ./

# Install packages, use --ignore-scripts to not call postinstall, as it causes this step to fail because config.json
# is not copied yet, and copying it here will trigger new install if config changes, which is inconvenient for development.
RUN yarn install --ignore-scripts --verbose

COPY --chown=${CONTAINER_USER}:root ./frontend/docker/dev/.env .
COPY --chown=${CONTAINER_USER}:root ./frontend .

# Copy config.json to docker root, because app scripts read it from ".."
COPY --chown=${CONTAINER_USER}:root ./config.json /
# Copy vesion.json to docker root, because app scripts read it from ".."
COPY --chown=${CONTAINER_USER}:root ./version.json /

# Disable linting before starting the server
ENV DISABLE_ESLINT_PLUGIN=true

# Set the port to serve the application
ENV PORT=80

CMD yarn start
