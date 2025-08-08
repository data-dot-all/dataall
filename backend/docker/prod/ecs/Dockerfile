FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=22
ARG NVM_VERSION=v0.40.3
ARG DEEQU_VERSION=2.0.7-spark-3.3
# setting a default but should be overridden by the build command
ARG PYTHON_VERSION=python3.12
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser
ARG CONTAINER_UID=999
ARG PORT=8080

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
RUN dnf install -y ${PYTHON_VERSION}
RUN dnf -y install ${PYTHON_VERSION}-pip ${PYTHON_VERSION}-devel

# Install AWS CLI
RUN <<-EOF
    curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip
    unzip -q /tmp/awscliv2.zip -d /opt
    /opt/aws/install --update -i /usr/local/aws-cli -b /usr/local/bin
    rm /tmp/awscliv2.zip
    rm -rf /opt/aws
    aws --version
EOF

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -u ${CONTAINER_UID} -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local
RUN mkdir -p /tmp
VOLUME ["/tmp"]
RUN chown -R ${CONTAINER_USER}:root /tmp

USER ${CONTAINER_USER}

# Configuring path
RUN touch ~/.bashrc

# Configuring Node and CDK
RUN <<-EOF
    curl -o- https://raw.githubusercontent.com/creationix/nvm/$NVM_VERSION/install.sh | bash
    . ~/.nvm/nvm.sh
    nvm install $NODE_VERSION
    nvm use $NODE_VERSION
    nvm alias default node
    nvm cache clear
    npm install -g aws-cdk
EOF

# App specific requirements
ADD --chown=${CONTAINER_USER}:root backend/requirements.txt /requirements.txt
ADD --chown=${CONTAINER_USER}:root backend/dataall/base/cdkproxy/requirements.txt /cdk.requirements.txt

# Install App requirements
RUN ${PYTHON_VERSION} -m pip install setuptools --prefix=/usr/local
RUN ${PYTHON_VERSION} -m pip install -r requirements.txt --prefix=/usr/local
RUN ${PYTHON_VERSION} -m pip install -r cdk.requirements.txt --prefix /usr/local

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

COPY --chmod=755 <<EOT /uvicorn.sh
#!/usr/bin/env bash
set -e
. ~/.nvm/nvm.sh
${PYTHON_VERSION} -m uvicorn --port ${PORT} \$@
EOT

CMD ["/uvicorn.sh", "cdkproxymain:app", "--host", "0.0.0.0"]
