from langchain_aws import ChatBedrock as BedrockChat
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dataall.base.aws.sts import SessionHelper


class UnstructuredBedrockClient:
    def __init__(self, account_id: str, region: str):
        self.__account_id = account_id
        self.__session = SessionHelper.get_session()

        self._client = self.__session.client('bedrock-runtime', region_name=region)
        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        model_kwargs = {
            'max_tokens': 190_000,
            'temperature': 0,
            'top_k': 250,
            'top_p': 1,
            'stop_sequences': ['\n\nHuman'],
        }

        self.__model = BedrockChat(
            client=self._client,
            model_id=model_id,
            model_kwargs=model_kwargs,
        )

    def invoke_model(self, prompt: str, content: str):
        messages = [
            (
                'system',
                """ You'll be given a document and a prompt from the user based on the information in the document I want you to follow the following steps:
            1. Detetermine if the document has the information to be able to answer the question. If not respond with "Error: The Document does not provide the information needed to answer you question"
            2. I want you to answer the question based on the information in the document.
            3. At the bottom I want you to provide the sources (the parts of the document where you found it). They should be listed in order
        <document>
        {content}
        </document>

        """,
            ),
            ('human', prompt),
        ]
        prompts = ChatPromptTemplate.from_messages(messages)

        chain = prompts | self.__model | StrOutputParser()
        response = chain.invoke({'question': prompt, 'content': content})
        return response
