FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG NODE_VERSION=16
ARG NVM_VERSION=v0.37.2
ARG DEEQU_VERSION=2.0.0-spark-3.1
ARG PYTHON_VERSION=python3.8
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser



# Installing libraries
RUN yum upgrade -y \
    && find /var/tmp -name "*.rpm" -print -delete \
    && find /tmp -name "*.rpm" -print -delete \
    && yum autoremove -y \
    && yum clean all \
    && rm -rfv /var/cache/yum \
    && yum install -y \
    shadow-utils wget openssl-devel bzip2-devel libffi-devel \
    postgresql-devel gcc unzip tar gzip \
    && amazon-linux-extras install $PYTHON_VERSION \
    && yum install -y python38-devel git \
    && /bin/bash -c "ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3" \
    && curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install --update -i /usr/local/aws-cli -b /usr/local/bin \
    && rm /tmp/awscliv2.zip \
    && rm -rf /opt/aws \
    && aws --version

RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN chown -R ${CONTAINER_USER}:root /usr/local

USER ${CONTAINER_USER}

# Configuring path
RUN touch ~/.bashrc

# Configuring Node and CDK
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/$NVM_VERSION/install.sh | bash \
    && /bin/bash -c ". ~/.nvm/nvm.sh && \
    nvm install $NODE_VERSION && nvm use $NODE_VERSION && \
    npm install -g aws-cdk && \
    nvm alias default node && nvm cache clear" \
    && echo export PATH="\
    /root/.nvm/versions/node/${NODE_VERSION}/bin:\
    $(${PYTHON_VERSION} -m site --user-base)/bin:\
    $(python3 -m site --user-base)/bin:\
    $PATH" >> ~/.bashrc && \
     echo "nvm use ${NODE_VERSION} 1> /dev/null" >> ~/.bashrc \
    && /bin/bash -c  ". ~/.nvm/nvm.sh && cdk --version"

RUN $PYTHON_VERSION -m pip install -U pip

# App specific
ADD --chown=${CONTAINER_USER}:root backend/requirements.txt /dh.requirements.txt
ADD --chown=${CONTAINER_USER}:root backend/dataall/base/cdkproxy/requirements.txt /cdk.requirements.txt

RUN /bin/bash -c "pip3.8 install -r /dh.requirements.txt --prefix /usr/local" \
    && /bin/bash -c "pip3.8 install -r /cdk.requirements.txt --prefix /usr/local"

ADD --chown=${CONTAINER_USER}:root backend/dataall /dataall
VOLUME ["/dataall"]
ADD backend/cdkproxymain.py /cdkproxymain.py

ENV config_location="/config.json"
COPY --chown=${CONTAINER_USER}:root config.json /config.json

RUN mkdir -p dataall/modules/datasets/cdk/assets/glueprofilingjob/jars/
ADD --chown=${CONTAINER_USER}:root https://repo1.maven.org/maven2/com/amazon/deequ/deequ/$DEEQU_VERSION/deequ-$DEEQU_VERSION.jar /dataall/modules/datasets/cdk/assets/glueprofilingjob/jars/

WORKDIR /

CMD [ "/bin/bash", "-c", ". ~/.nvm/nvm.sh && uvicorn cdkproxymain:app --host 0.0.0.0 --port 8080" ]

