FROM postgres:10

ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /var/lib/
RUN chown -R ${CONTAINER_USER}:root /var/run/
RUN chown -R ${CONTAINER_USER}:root /tmp
USER ${CONTAINER_USER}
