import logging
import os
from dataall.base.config import config
from dataall.base.aws.sts import SessionHelper
from langchain_aws import BedrockLLM
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.output_parsers import JsonOutputParser

log = logging.getLogger(__name__)


#  TODO session for infra account - should we use a dedicated role?
class BedrockClient:
    def __init__(self):
        session = SessionHelper.get_session()
        self._client = session.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        self._model_id = config.get_property('modules.s3_datasets.features.generate_metadata_ai.model_id')
        ## TODO experiment with optimal params
        # {
        #     'anthropic_version': 'bedrock-2023-05-31',
        #     'max_tokens': 4096,
        #     'messages': messages,
        #     'temperature': 0.5,
        #     'top_p': 0.5,
        #     'stop_sequences': ['\n\nHuman:'],
        #     'top_k': 250,
        # }
        model_kwargs = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 4096,
            'temperature': 0,
        }
        self._llm = BedrockLLM(model_id=self._model_id, client=self._client, model_kwargs=model_kwargs)

    def invoke_model(self, prompt_template: PromptTemplate, prompt: str, output_object: BaseModel):
        parser = JsonOutputParser(pydantic_object=output_object)
        chain = prompt_template | self._llm | parser
        return chain.invoke(prompt)
