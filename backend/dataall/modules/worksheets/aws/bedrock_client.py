from dataall.base.aws.sts import SessionHelper
from langchain_aws import ChatBedrock as BedrockChat
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dataall.modules.worksheets.aws.bedrock_prompts import (
    SQL_EXAMPLES,
    TEXT_TO_SQL_PROMPT_TEMPLATE,
    PROCESS_TEXT_PROMPT_TEMPLATE,
)


class BedrockClient:
    def __init__(self):
        self._session = SessionHelper.get_session()
        self._client = self._session.client('bedrock-runtime')
        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        model_kwargs = {
            'max_tokens': 2048,
            'temperature': 0,
            'top_k': 250,
            'top_p': 1,
            'stop_sequences': ['\n\nHuman'],
        }
        self._model = BedrockChat(
            client=self._client,
            model_id=model_id,
            model_kwargs=model_kwargs,
        )

    def invoke_model_text_to_sql(self, prompt: str, metadata: str):
        prompt_template = PromptTemplate.from_template(TEXT_TO_SQL_PROMPT_TEMPLATE)

        chain = prompt_template | self._model | StrOutputParser()
        response = chain.invoke({'prompt': prompt, 'context': metadata, 'examples': SQL_EXAMPLES})
        return response

    def invoke_model_process_text(self, prompt: str, content: str):
        prompt_template = PromptTemplate.from_template(PROCESS_TEXT_PROMPT_TEMPLATE)

        chain = prompt_template | self._model | StrOutputParser()
        response = chain.invoke({'prompt': prompt, 'content': content})
        return response
