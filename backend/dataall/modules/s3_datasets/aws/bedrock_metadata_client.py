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
    def generate_metadata(self, table, table_column): #enforce type annotations , metadata_query_result -> table
        log.info("Generating metadata for table %s", table_column.GlueTableName)
        prompt_data = f"""
        Generate a detailed metadata description for a database table named {table_column.GlueTableName} using following provided data: 
              table name, 
              columns: {','.join(table_column.label)}
              Try to use following inputs as well but do not use these data if it says: "No description provided" for generation
              current column descriptions: ({','.join(table_column.description)}) 
              table_description: {table.description if table.description else ''}
              table_label: {table.label if table.label else ''}

              Your goal is generate Tags,Topic, Description for this table using above data and your knowledge. Return a string that looks like this:
              This dataset is about <topic>. It contains the following columns: <column1>, <column2>, ..., <columnN>.
              The table name is <table_name>.
              The table tags are <tags>.
              The table description is: <description>.
              Descripton for each column is 
                        <column1>:<column1_description>,
                        <column2>:<column2_description>
                        ,...,
                        <columnN>:<columnN_description>.
              Decide if there were enough data provided to you to generate metadata.
               Return only the string, no additional text or explanation. If there not enough metadata please return "NotEnoughData".
        """
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
        log.info("Bedrock says: \n %s",output_str)
        return output_str
    '''
        # Parse the output string to extract the required information

        # pattern = r"This dataset is about (.*?)\. It contains the following columns: (.*?)\.\s*The table name is (.*?)\.\s*The table tags are (.*?)\.\s*The table description is: (.*?)\.\s*Descripton for each column is (.*?)\."
        # match = re.search(pattern, output_str, re.DOTALL)

     
        # topic = match.group(1)
        # columns_str = match.group(2)
        # table_name = match.group(3)
        # tags = match.group(4)
        # description = match.group(5)
        # columns_description = match.group(6)

        # return {
        #     'Topic': topic,
        #     'TableName': table_name,
        #     'Tags': tags,
        #     'Columns': columns_str,
        #     'ColumnsDescription': columns_description,
        #     'Description': description     
        # }
       
     '''