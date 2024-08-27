import logging
import json
import re
from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
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
            'subitem_descriptions': kwargs.get('subitem_descriptions', []),
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
        if prompt_type == 'Table':
            return f"""
             Generate or improve metadata for a common_data['label'] table using the following provided data:
                - Table name: {common_data['label'] if common_data['label'] else 'No description provided'}
                - Column names: {common_data['columns'] if common_data['columns'] else 'No description provided'}
                - Table description: {common_data['description'] if common_data['description'] else 'No description provided'}
                - Tags: {common_data['tags'] if common_data['tags'] else 'No description provided'}
                - Subitem Descriptions: {common_data['subitem_descriptions'] if common_data['subitem_descriptions'] else 'No description provided'}
                - (Only Input) Sample data: {common_data['sample_data'] if common_data['sample_data'] else 'No sample data'}
                **Important**: 
                - If the data indicates "No description provided," do not use that particular input for generating metadata, these data is optional you should still generate in that case.
                - Only focus on generating the following metadata types as specified by the user: {common_data['metadata_types']}. Do not include any other metadata types.
                - Sample data is only input for you to understand the table better, do not generate sample data.
                Your response must strictly contain all the requested metadata types, do not include any of the metadata types if it is not specified by the user. Don't use ' ' in your response, use " ".
                Subitem Descriptions corresponds to column descriptions. If the user specifically didn't ask for subitem descriptions, do not include it in the response.     
                subitem_descriptions is another dictionary within the existing dictionary, rest of them are strings, never change order of columns when you generate description for them.
                For example, if the requested metadata types are "Tags" and "Subitem Descriptions", the response should be:
                tags: <tags>
                subitem_descriptions: 
                    <column1 label>:<column1_description>
                    <column2 label>:<column2_description>
                    ,...,
                    <columnN>:<columnN_description>
                Evaluate if the given parameters are sufficient for generating the requested metadata, if not, respond with "NotEnoughData" for all values of dictionary keys.
                Return the result as a Python dictionary where the keys are the requested metadata types, all the keys must be lowercase and the values are the corresponding generated metadata. 
                For tags and topics, ensure the output is a string list.  Label is singular so you should return only one label as string.

            """
 
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
                Evaluate if the given parameters are sufficient for generating the requested metadata, if not, respond with listing table names and folder names for description and for label keep the current name
                For tags and topics, ensure the output is a string list.  Label is singular so you should return only one label as string. 
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
              For tags and topics, ensure the output is a string list. Label is singular so you should return only one label as string.
              Return a python dictionary, all the keys must be lowercase. Don't use ' ' in your response, use " ".   Include file types as pdf, and write file names in description.
              Evaluate if the given parameters are sufficient for generating the requested metadata, if not, respond with "NotEnoughData" for all values of dictionary keys.
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
    
    def _parse_response(self, response_content, targetName, subitem_ids ):
        output_str = response_content[0]['text']


        output_dict = json.loads(output_str)
        if not output_dict.get("name"):
            output_dict["name"] = targetName
        
        if output_dict.get('subitem_descriptions'):
            subitem_ids = subitem_ids.pop()
            subitem_ids = subitem_ids.split(',')
            subitem_ids = subitem_ids[:len(output_dict["subitem_descriptions"])]
            subitem_descriptions = []
            for index, (key, value) in enumerate(output_dict["subitem_descriptions"].items()):
                subitem_descriptions.append({
                    "label": key,
                    "description": value,
                    "subitem_id": subitem_ids[index]
                })
            output_dict["subitem_descriptions"] = subitem_descriptions
        return output_dict
  
    def generate_metadata(self, **kwargs):
        prompt = self._generate_prompt(**kwargs)
        response_content = self._invoke_model(prompt)
        return self._parse_response(response_content, kwargs.get('label', ' '), kwargs.get('subitem_ids', ' '))