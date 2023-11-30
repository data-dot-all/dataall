FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ARG NODE_VERSION=18
ARG NVM_VERSION=v0.37.2
ARG PYTHON_VERSION=python3.8

RUN dnf clean all
RUN dnf -y install shadow-utils wget
RUN dnf -y install openssl-devel bzip2-devel libffi-devel postgresql-devel gcc unzip tar gzip
RUN dnf install $PYTHON_VERSION
RUN dnf -y install python38-devel
RUN dnf -y install git

RUN /bin/bash -c "ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3"

RUN useradd -m app

WORKDIR /build

RUN touch ~/.bashrc

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

COPY ./docker/dev/wait-for-it.sh /build/wait-for-it.sh
RUN chmod +x /build/wait-for-it.sh
RUN chown -R app:root /build/wait-for-it.sh

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
$PATH" >> ~/.bashrc && \
     echo "nvm use ${NODE_VERSION} 1> /dev/null" >> ~/.bashrc

RUN /bin/bash -c  ". ~/.nvm/nvm.sh && cdk --version"

COPY ./requirements.txt dh.requirements.txt
COPY ./dataall/base/cdkproxy/requirements.txt cdk.requirements.txt
COPY ./dataall /dataall

ADD ./cdkproxymain.py /cdkproxymain.py
ADD ./local_graphql_server.py /local_graphql_server.py

RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -U pip "
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r dh.requirements.txt"
RUN /bin/bash -c "${PYTHON_VERSION} -m pip install -r cdk.requirements.txt"

WORKDIR /

ENTRYPOINT [ "/bin/bash", "-c", ". ~/.nvm/nvm.sh && uvicorn cdkproxymain:app --host 0.0.0.0 --port 8080" ]
