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

    '''Inputs:
        * table label in data.all 
        * current description in data.all 
        * Glue columns names
        * Glue columns descriptions
        * Glue table name'''
    def generate_metadata_table(self, table, table_column): #enforce type annotations , metadata_query_result -> table
        log.info("Generating metadata for table %s", table_column.GlueTableName)
        #if table this the prompt
        prompt_data = f"""
        Generate a detailed metadata description for a database table using following provided data: 
              folder name: {table.label}, 
              column names: {','.join(table_column.label)} 
              Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
              current column descriptions: ({','.join(table_column.description)}) 
              table_description: {table.description if table.description else ''}
              table_label: {table.label if table.label else ''}
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
        #if dataset there will be another prompt
        #if folder there will be another prompt

        log.info("Prompt data: \n %s", prompt_data)
      
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
        
        #modelId = "anthropic.claude-3-haiku-20240307-v1:0"#quota limit? Haiku: cheaper
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = self._client.invoke_model(body=body, modelId=modelId)
        response_body = json.loads(response.get('body').read())
        output_list = response_body.get("content", [])
        output_str = output_list[0]['text']
        output_dict = json.loads(output_str)
        output_dict["Column_Descriptions"] = [{ "Column_Name": key, "Column_Description": value} for key, value in output_dict["Column_Descriptions"].items()]
        return output_dict

    
    def generate_metadata_dataset(self, dataset, tabels): #enforce type annotations , metadata_query_result -> table
        prompt_data = f"""
        Generate a detailed metadata description for a database table using following provided data: 
              table name: {dataset.label}, 
              tables: {tabels} 
              Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
              table_description: {dataset.description if dataset.description else ''}
              table_label: {dataset.label if dataset.label else ''}
              Your goal is generate Tags,Topic, Description and column descriptions for this table using above data and with your knowledge.  All the parameters you return has value String. Return:
              Topic: <topic>. 
              TableName: <table_name>
              Tags: <tags>
              Description: <description>
             
              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".  Return a python dictionary.
         """
        #if dataset there will be another prompt
        #if folder there will be another prompt

        log.info("Prompt data: \n %s", prompt_data)
      
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
        
        #modelId = "anthropic.claude-3-haiku-20240307-v1:0"#quota limit? Haiku: cheaper
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = self._client.invoke_model(body=body, modelId=modelId)
        response_body = json.loads(response.get('body').read())
        output_list = response_body.get("content", [])
        output_str = output_list[0]['text']
        output_dict = json.loads(output_str)
        return output_dict
       
    def generate_metadata_folder(self, folder, file_names): #enforce type annotations , metadata_query_result -> table
        prompt_data = f"""
        Generate a detailed metadata description for a database table using following provided data: 
              folder name: {folder.label}, 
              file names: {file_names} 
              Try to use following inputs as well, but do not use these data if it says: "No description provided" for generation
              folder_description: {folder.description if folder.description else ''}
              folder_tags: {folder.tags if folder.tags else ''}
              Your goal is generate Description and Tags for this folder using above data and with your knowledge. All the parameters you return has value String. Return:
              Description: <description>
              Tags: <tags>

              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".  Return a python dictionary.
         """
        #if dataset there will be another prompt
        #if folder there will be another prompt


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

        #modelId = "anthropic.claude-3-haiku-20240307-v1:0"#quota limit? Haiku: cheaper
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = self._client.invoke_model(body=body, modelId=modelId)
        response_body = json.loads(response.get('body').read())
        output_list = response_body.get("content", [])
        output_str = output_list[0]['text']
        output_dict = json.loads(output_str)
        log.info("Prompt data: \n %s", output_dict)

        return output_dict

    def generate_metadata_column(self, table_column): #enforce type annotations , metadata_query_result -> table
        prompt_data = f"""
        Generate a detailed metadata description for a database table using following provided data:
              column name: {table_column.label},
              column_description: {table_column.description if table_column.description else ''}e using above data and with your knowledge. All the parameters you return has value String. Return:
              Tags: <tags>
              Description: <description>
             
              Evaluate if the given parameters are enough for generating metadata, if not response should be: "NotEnoughData".  Return a python dictionary.
         """
        #if dataset there will be another prompt
        #if folder there will be another prompt

        log.info("Prompt data: \n %s", prompt_data)
      
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
        
        #modelId = "anthropic.claude-3-haiku-20240307-v1:0"#quota limit? Haiku: cheaper
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
        response = self._client.invoke_model(body=body, modelId=modelId)
        response_body = json.loads(response.get('body').read())
        output_list = response_body.get("content", [])
        output_str = output_list[0]['text']
        output_dict = json.loads(output_str)
        return output_dict