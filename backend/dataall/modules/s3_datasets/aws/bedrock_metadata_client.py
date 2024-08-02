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
        prompt_type = kwargs.get('prompt_type', 'Table')
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
            'tables': kwargs.get('tables', []),
            'table_description' : kwargs.get('table_descriptions', ''),
            'metadata_types' : kwargs.get('metadata_type', []),
            'folders': kwargs.get('folders', []),
            'sample_data': kwargs.get('sample_data', [])
            }
        log.info("metadata", common_data['metadata_types'])
        if prompt_type == 'Table':
            return f"""
             Generate or improve metadata for a common_data['label'] table using the following provided data:
                - Table name: {common_data['label'] if common_data['label'] else 'No description provided'}
                - Column names: {common_data['columns'] if common_data['columns'] else 'No description provided'}
                - Table description: {common_data['description'] if common_data['description'] else 'No description provided'}
                - Tags: {common_data['tags'] if common_data['tags'] else 'No description provided'}
                - (Only Input) Sample data: {common_data['sample_data'] if common_data['sample_data'] else 'No sample data'}
                **Important**: 
                - If the data indicates "No description provided," do not use that particular input for generating metadata, these data is optional you should still generate in that case.
                - Only focus on generating the following metadata types as specified by the user: {common_data['metadata_types']}. Do not include any other metadata types.
                - Sample data is only input for you to understand the table better, do not generate sample data.
                Your response must strictly contain all the requested metadata types, do not include any of the metadata types if it is not specified by the user. Don't use ' ' in your response, use " ".
                For example, if the requested metadata types are "Tags", the response should be:
                tags: <tags>
                Evaluate if the given parameters are sufficient for generating the requested metadata. If not, respond with "NotEnoughData".
                Return the result as a Python dictionary where the keys are the requested metadata types, all the keys must be lowercase and the values are the corresponding generated metadata. 
                For tags, ensure the output is a string without "[" or "]".
            """
        #             Column_Descriptions: 
        #                         <column1>:<column1_description>
        #                         <column2>:<column2_description>
        #                             ,...,
        #                         <columnN>:<columnN_description>
        #Column_Descriptions is another dictionary within the existing dictionary, rest of them are strings.
        #- Column descriptions: ({common_data['column_descriptions'] if common_data['column_descriptions'] else 'No description provided'})
        elif prompt_type == 'S3_Dataset':
            return f"""
              Generate or improve metadata for a dataset using the following provided data:
                - Dataset name: {common_data['label'] if common_data['label'] else 'No description provided'}
                - Table names in the dataset: {common_data['tables'] if common_data['tables'] else 'No description provided'}
                - Folder names in the dataset: {common_data['folders'] if common_data['folders'] else 'No description provided'}
                - Current tags for dataset: {common_data['tags'] if common_data['tags'] else 'No description provided'}
                - Current dataset description: {common_data['description'] if common_data['description'] else 'No description provided'}
                **Important**: 
                    - If the data indicates "No description provided," do not use that particular input for generating metadata.
                    - Only focus on generating the following metadata types as specified by the user: {common_data['metadata_types']}. Do not include any other metadata types.
                    - Return the result as a Python dictionary.
                Your response should strictly contain the requested metadata types. Don't use ' ' in your response, use " ".
                For example, if the requested metadata types are "tags" and "description", the response should be:
                    "tags":<tags>
                    "description":<description>
                Evaluate if the given parameters are sufficient for generating the requested metadata. If not, respond with "NotEnoughData".
                For tags, ensure the output is a string without "[" or "]".
                Return the result as a Python dictionary where the keys are the requested metadata types, all the keys must be lowercase and the values are the corresponding generated metadata.

            """
        elif prompt_type == 'Folder':
            return f"""
              Generate a detailed metadata description for a database table using following provided data: 
              folder name: {common_data['label']}, 
              file names: {common_data['file_names'] if common_data['file_names'] else 'No description provided'} 
              folder_description: {common_data['description'] if common_data['description'] else 'No description provided'}
              folder_tags: {common_data['tags'] if common_data['tags'] else 'No description provided'}
                **Important**: 
                    - If the data indicates "No description provided," do not use that particular input for generating metadata.
                    - Only focus on generating the following metadata types as specified by the user: {common_data['metadata_types']}. Do not include any other metadata types.
                    - Return the result as a Python dictionary.
              Your response should strictly contain the requested metadata types.
              For example, if the requested metadata types are "tags" and "description", the response should be:
                  "tags":<tags>
                  "description":<description>
              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".    Your response should strictly contain the requested metadata types. 
              For tags, ensure the output is a string without "[" or "]".
              Return a python dictionary, all the keys must be lowercase. Don't use ' ' in your response, use " ".
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
        log.info("Prompt response: \n %s", response_body)
        return response_body.get("content", [])
    
    def _parse_response(self, response_content, targetName ):
        output_str = response_content[0]['text']
        log.info("Prompt output: \n %s", output_str)

        
        output_dict = json.loads(output_str)
        if not output_dict.get("name"):
            output_dict["name"] = targetName
            
        log.info("Prompt output dict: \n %s", output_dict)
        # if output_dict.get('Column_Descriptions'):
        #     output_dict["Column_Descriptions"] = [
        #         {"Column_Name": key, "Column_Description": value}
        #         for key, value in output_dict["Column_Descriptions"].items()
        #     ]
        return output_dict
  
    def generate_metadata(self, **kwargs):
        prompt = self._generate_prompt(**kwargs)
        log.info("Prompt: \n %s", prompt)
        response_content = self._invoke_model(prompt)
        return self._parse_response(response_content, kwargs.get('label', ' '))