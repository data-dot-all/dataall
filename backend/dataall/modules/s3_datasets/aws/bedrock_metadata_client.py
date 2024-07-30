import logging
import json
import re
from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region,role='arn:aws:iam::637423548259:role/pelin-demo-role')
        self._client = session.client('bedrock-runtime', region_name=region)
        self._account_id = account_id
        self.region = region
  
    def _generate_prompt(self, **kwargs):
        prompt_type = kwargs.get('prompt_type', 'table')
        common_data = {
            'label': kwargs.get('label', ''),
            'description': kwargs.get('description', ''),
            'tags': kwargs.get('tags', ''),
            'columns': kwargs.get('columns', []),
            'column_descriptions': kwargs.get('column_descriptions', []),
            'file_names': kwargs.get('file_names', []),
            'folder_name': kwargs.get('folder_name', ''),
            'folder_description': kwargs.get('folder_description', ''),
            'folder_tags': kwargs.get('folder_tags', ''),
            'tables': kwargs.get('tables', ''),
            'table_description' : kwargs.get('table_descriptions', '')
            }

        if prompt_type == 'Table':
            return f"""
            Generate a detailed metadata description for a database table using following provided data: 
                table name: {common_data['label']}, 
                column names: {common_data['columns']} 
                Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
                current column descriptions: ({common_data['column_descriptions']}) 
                table_description: {common_data['description'] if common_data['description'] else ''}
                tags : {common_data['tags'] if common_data['tags'] else ''}
                Your goal is generate Tags,Topic, Description and column descriptions for this table using above data and with your knowledge. All the parameters you return has value String. Return:
                Topic: <topic>. 
                TableName: <table_name>
                Tags: <tags>
                Description: <description>
                Column_Descriptions: 
                <column1>:<column1_description>
                <column2>:<column2_description>
                    ,...,
                <columnN>:<columnN_description>
                
                Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".  Return a python dictionary. Column_Descriptions is another dictionary within the existing dictionary, rest of them are strings.
            """
        elif prompt_type == 'S3_Dataset':
            return f"""
              Generate a detailed metadata description for a database table using following provided data: 
              dataset name: {common_data['label']}, 
              table names in the dataset: {common_data['tables']} 
              Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
              table descriptions: {common_data['table_description']}
              tags: {common_data['tags'] if common_data['tags'] else ''}
              Generate meaningful Tags,Topic, Description and column descriptions for this table using above data and with your knowledge. 
              All the parameters you return has value String! Return:
              Tags:
              Description: 
              Topic:
              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData". 
              Return a python dictionary.
         """
        elif prompt_type == 'Folder':
            return f"""
              Generate a detailed metadata description for a database table using following provided data: 
              folder name: {common_data['label']}, 
              file names: {common_data['file_names']} 
              Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
              folder_description: {common_data['description'] if common_data['description'] else ''}
              folder_tags: {common_data['tags'] if common_data['tags'] else ''}
              Your goal is generate Description and Tags for this folder using above data and with your knowledge. All the parameters you return has value String. Return:
              Description: <description>
              Tags: <tags>

              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".  Return a python dictionary.
         """
    
    def _invoke_model(self, prompt):
        messages=[{ "role":'user', "content":[{'type':'text','text': prompt}]}]
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
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = self._client.invoke_model(body=body, modelId=modelId)
        response_body = json.loads(response.get('body').read())
        return response_body.get("content", [])
    
    def _parse_response(self, response_content):
        output_str = response_content[0]['text']
        log.info("Prompt data: \n %s", output_str)
        output_dict = json.loads(output_str)
        log.info("Prompt data: \n %s", output_dict)

        if output_dict.get('Column_Descriptions'):
            output_dict["Column_Descriptions"] = [
                {"Column_Name": key, "Column_Description": value}
                for key, value in output_dict["Column_Descriptions"].items()
            ]
        return output_dict
  
    def generate_metadata(self, **kwargs):
        prompt = self._generate_prompt(**kwargs)
        response_content = self._invoke_model(prompt)
        return self._parse_response(response_content)