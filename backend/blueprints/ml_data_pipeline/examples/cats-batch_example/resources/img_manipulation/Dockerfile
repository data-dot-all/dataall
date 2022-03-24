FROM public.ecr.aws/alexaprizesharedresources/python:3.7-slim-buster

ENV SOURCE_PATH /opt/program/source
RUN mkdir -p ${SOURCE_PATH}

#Set up source
COPY .  ${SOURCE_PATH}
RUN pip install -r ${SOURCE_PATH}/requirements.txt -t ${SOURCE_PATH}
RUN pip install  awscli --upgrade

#Set up working directory
WORKDIR ${SOURCE_PATH}
ENTRYPOINT  ["python", "main.py"]
