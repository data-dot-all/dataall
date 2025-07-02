FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=22
ARG NVM_VERSION=v0.37.2
ARG DEEQU_VERSION=2.0.7-spark-3.3
ARG PYTHON_VERSION=python3.9
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser

# Clean cache
RUN dnf upgrade -y;\
    find /var/tmp -name "*.rpm" -print -delete ;\
    find /tmp -name "*.rpm" -print -delete ;\
    dnf autoremove -y; \
    dnf clean all; rm -rfv /var/cache/dnf

# Installing libraries
RUN dnf -y install \
    shadow-utils wget openssl-devel bzip2-devel libffi-devel \
    postgresql-devel gcc unzip tar gzip

# Install Python
RUN dnf install $PYTHON_VERSION
RUN dnf -y install python3-pip python3-devel git

# Install AWS CLI
RUN curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install --update -i /usr/local/aws-cli -b /usr/local/bin \
    && rm /tmp/awscliv2.zip \
    && rm -rf /opt/aws \
    && aws --version

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local
RUN mkdir -p /tmp
VOLUME ["/tmp"]
RUN chown -R ${CONTAINER_USER}:root /tmp

USER ${CONTAINER_USER}

# Configuring path
RUN touch ~/.bashrc

# Configuring Node and CDK
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/$NVM_VERSION/install.sh | bash \
    && /bin/bash -c ". ~/.nvm/nvm.sh && \
    nvm install $NODE_VERSION && nvm use $NODE_VERSION && \
    npm install -g aws-cdk && \
    nvm alias default node && nvm cache clear"

RUN echo export PATH="\
    /root/.nvm/versions/node/${NODE_VERSION}/bin:\
    $(${PYTHON_VERSION} -m site --user-base)/bin:\
    $(python3 -m site --user-base)/bin:\
    $PATH" >> ~/.bashrc && \
     echo "nvm use ${NODE_VERSION} 1> /dev/null" >> ~/.bashrc \
    && /bin/bash -c  ". ~/.nvm/nvm.sh && cdk --version"

# App specific requirements
ADD --chown=${CONTAINER_USER}:root backend/requirements.txt /requirements.txt
ADD --chown=${CONTAINER_USER}:root backend/dataall/base/cdkproxy/requirements.txt /cdk.requirements.txt

# Install App requirements
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install setuptools --prefix /usr/local"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r requirements.txt --prefix /usr/local"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r cdk.requirements.txt --prefix /usr/local"

# App code
ADD --chown=${CONTAINER_USER}:root backend/dataall /dataall
VOLUME ["/dataall"]
ADD --chown=${CONTAINER_USER}:root backend/cdkproxymain.py /cdkproxymain.py

# App configuration file
ENV config_location="/config.json"
COPY --chown=${CONTAINER_USER}:root config.json /config.json

# Glue profiling jobs jars
RUN mkdir -p dataall/modules/datasets/cdk/assets/glueprofilingjob/jars/
ADD --chown=${CONTAINER_USER}:root https://repo1.maven.org/maven2/com/amazon/deequ/deequ/$DEEQU_VERSION/deequ-$DEEQU_VERSION.jar /dataall/modules/s3_datasets/cdk/assets/glueprofilingjob/jars/

WORKDIR /

CMD [ "/bin/bash", "-c", ". ~/.nvm/nvm.sh && uvicorn cdkproxymain:app --host 0.0.0.0 --port 8080" ]
