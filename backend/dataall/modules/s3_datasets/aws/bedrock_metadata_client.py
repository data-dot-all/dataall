import logging
import json

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region,role='arn:aws:iam::637423548259:role/pelin-demo-role')
        self._client = session.client('bedrock-runtime', region_name=region)
        self._account_id = account_id
        self.region = region
    def generate_metadata(self, table_name:str, columns:str): #enforce type annotations , metadata_query_result -> table
        log.info("Generating metadata for table %s", table_name)
        prompt_data = f"""
        Generate a detailed metadata description for a database table named {table_name} using table name and \
              columns({columns})following parameters and generate Tags,Topic, Description for this table. Return a string that looks like this:\
              This dataset is about <topic>. It contains the following columns: <column1>, <column2>, ..., <columnN>.\
              The table name is <table_name>.\
              The table tags are <tags>.\
              The table description is: <description>.\
              Descripton for each column is <column1>:<column1_description>,<column2>:<column2_description>,...,<columnN>:<columnN_description>.\
              Return only the string, no additional text or explanation.\
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
        log.info(output_list)

        output_str = output_list[0]['text']
        return output_str
   