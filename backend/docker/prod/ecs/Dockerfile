FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG NODE_VERSION=16
ARG NVM_VERSION=v0.37.2
ARG DEEQU_VERSION=2.0.0-spark-3.1
ARG PYTHON_VERSION=python3.8

RUN yum upgrade -y \
    && find /var/tmp -name "*.rpm" -print -delete \
    && find /tmp -name "*.rpm" -print -delete \
    && yum autoremove -y \
    && yum clean all \
    && rm -rfv /var/cache/yum

RUN yum install -y \
    shadow-utils wget openssl-devel bzip2-devel libffi-devel \
    postgresql-devel gcc unzip tar gzip \
    && amazon-linux-extras install $PYTHON_VERSION \
    && yum install -y python38-devel git

RUN /bin/bash -c "ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3"

# Install AWS CLI v2
# https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html
RUN curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install --update -i /usr/local/aws-cli -b /usr/local/bin \
    && rm /tmp/awscliv2.zip \
    && rm -rf /opt/aws \
    && aws --version

RUN touch ~/.bashrc

RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/$NVM_VERSION/install.sh | bash

RUN /bin/bash -c ". ~/.nvm/nvm.sh && \
    nvm install $NODE_VERSION && nvm use $NODE_VERSION && \
    npm install -g aws-cdk && \
    nvm alias default node && nvm cache clear"

RUN echo export PATH="\
/root/.nvm/versions/node/${NODE_VERSION}/bin:\
$(${PYTHON_VERSION} -m site --user-base)/bin:\
$(python3 -m site --user-base)/bin:\
$PATH" >> ~/.bashrc && \
     echo "nvm use ${NODE_VERSION} 1> /dev/null" >> ~/.bashrc
RUN /bin/bash -c  ". ~/.nvm/nvm.sh && cdk --version"

RUN $PYTHON_VERSION -m pip install -U pip

ADD backend/requirements.txt /dh.requirements.txt
ADD backend/dataall/cdkproxy/requirements.txt /cdk.requirements.txt

RUN /bin/bash -c "pip3.8 install -r /dh.requirements.txt" \
    && /bin/bash -c "pip3.8 install -r /cdk.requirements.txt"

ADD backend/dataall /dataall
ADD backend/blueprints /blueprints
ADD backend/cdkproxymain.py /cdkproxymain.py

RUN mkdir -p dataall/cdkproxy/assets/glueprofilingjob/jars \
    && mkdir -p blueprints/ml_data_pipeline/engine/glue/jars \
    && curl https://repo1.maven.org/maven2/com/amazon/deequ/deequ/$DEEQU_VERSION/deequ-$DEEQU_VERSION.jar --output dataall/cdkproxy/assets/glueprofilingjob/jars/deequ-$DEEQU_VERSION.jar \
    && cp -f dataall/cdkproxy/assets/glueprofilingjob/jars/deequ-$DEEQU_VERSION.jar blueprints/ml_data_pipeline/engine/glue/jars/deequ-$DEEQU_VERSION.jar

WORKDIR /

CMD [ "/bin/bash", "-c", ". ~/.nvm/nvm.sh && uvicorn cdkproxymain:app --host 0.0.0.0 --port 8080" ]
