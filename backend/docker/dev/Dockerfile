FROM public.ecr.aws/amazonlinux/amazonlinux:2

ARG NODE_VERSION=16
ARG NVM_VERSION=v0.37.2
ARG PYTHON_VERSION=python3.8
ARG CONTAINER_USER=cuser
ARG CONTAINER_USER_GROUP=cuser



RUN yum clean all
RUN yum -y install shadow-utils wget
RUN yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN amazon-linux-extras install $PYTHON_VERSION
RUN yum -y install python38-devel
RUN yum -y install git

RUN /bin/bash -c "ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3"
RUN groupadd -r ${CONTAINER_USER_GROUP} && useradd -m -r -g ${CONTAINER_USER_GROUP} ${CONTAINER_USER}
RUN useradd -m app
RUN chown -R ${CONTAINER_USER}:root /usr/local

USER ${CONTAINER_USER}


WORKDIR /build

RUN touch ~/.bashrc

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

COPY --chown=${CONTAINER_USER}:root ./docker/dev/wait-for-it.sh /build/wait-for-it.sh
RUN chmod +x /build/wait-for-it.sh
RUN chown -R ${CONTAINER_USER}:root /build/wait-for-it.sh

WORKDIR /dataall
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
$(python -m site --user-base)/bin:\
/home/${CONTAINER_USER}/.local/bin:\
$PATH" >> ~/.bashrc && \
     echo "nvm use ${NODE_VERSION} 1> /dev/null" >> ~/.bashrc

RUN /bin/bash -c  ". ~/.nvm/nvm.sh && cdk --version"

COPY ./requirements.txt dh.requirements.txt
COPY ./dataall/base/cdkproxy/requirements.txt cdk.requirements.txt
COPY ./dataall /dataall

ADD ./cdkproxymain.py /cdkproxymain.py
ADD ./local_graphql_server.py /local_graphql_server.py

RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -U pip --prefix /usr/local"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r dh.requirements.txt --prefix /usr/local"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r cdk.requirements.txt --prefix /usr/local"

WORKDIR /

ENTRYPOINT [ "/bin/bash", "-c", ". ~/.nvm/nvm.sh && uvicorn cdkproxymain:app --host 0.0.0.0 --port 8080" ]
