import logging
import json

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = session.client('bedrock-runtime', region_name=region)
        self._account_id = account_id
        self.region = region

    def generate_metadata(self, metadata_query_result):
        if metadata_query_result:
            columns, table_name = metadata_query_result
            prompt_data = f"""
            Generate a detailed metadata description for a database table in the following form.
            Table Name: {table_name}
            Columns: {columns}
            Tags:
            Topic:
            Description:
            """
            messages=[{ "role":'user', "content":[{'type':'text','text': prompt_data}]}]
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": messages,
                    "temperature": 0.5,
                    "top_p": 0.5,
                    "stop_sequences": ["\n\nHuman:"],
                    "top_k":250
                }  
            )  
            modelId = "anthropic.claude-3-sonnet-20240229-v1:0"#quota limit? Haiku: cheaper
            response = self._client.invoke_model(body=body, modelId=modelId)
            response_body = json.loads(response.get('body').read())
            output_list = response_body.get("content", [])
            return output_list
        else:
            log.info(f'No metadata query result for account {self._account_id}')
            return None