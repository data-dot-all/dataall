ARG ELK_VERSION


# https://www.docker.elastic.co/
FROM docker.elastic.co/elasticsearch/elasticsearch:${ELK_VERSION}

ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/share/elasticsearch
USER ${CONTAINER_USER}



# Add your elasticsearch plugins setup here
# Example: RUN elasticsearch-plugin install analysis-icu
