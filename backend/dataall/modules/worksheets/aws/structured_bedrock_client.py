from dataall.base.aws.sts import SessionHelper
from langchain_aws import ChatBedrock as BedrockChat
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

examples = [
    {
        'User': """I want to get the average area of all listings \\n\\nBased on on the following glue metadata: \n            
    <context>
    Database Name : dataall_homes_11p3uu8f
    Table name: listings 
                Column Metadata: [{'Name': 'price', 'Type': 'bigint'}, {'Name': 'area', 'Type': 'bigint'}, {'Name': 'bedrooms', 'Type': 'bigint'}, {'Name': 'bathrooms', 'Type': 'bigint'}, {'Name': 'stories', 'Type': 'bigint'}, {'Name': 'mainroad', 'Type': 'string'}, {'Name': 'guestroom', 'Type': 'string'}, {'Name': 'basement', 'Type': 'string'}, {'Name': 'hotwaterheating', 'Type': 'string'}, {'Name': 'airconditioning', 'Type': 'string'}, {'Name': 'parking', 'Type': 'bigint'}, {'Name': 'prefarea', 'Type': 'string'}, {'Name': 'furnishingstatus', 'Type': 'string'}, {'Name': 'passengerid', 'Type': 'bigint'}, {'Name': 'survived', 'Type': 'bigint'}, {'Name': 'pclass', 'Type': 'bigint'}, {'Name': 'name', 'Type': 'string'}, {'Name': 'sex', 'Type': 'string'}, {'Name': 'age', 'Type': 'double'}, {'Name': 'sibsp', 'Type': 'bigint'}, {'Name': 'parch', 'Type': 'bigint'}, {'Name': 'ticket', 'Type': 'string'}, {'Name': 'fare', 'Type': 'double'}, {'Name': 'cabin', 'Type': 'string'}, {'Name': 'embarked', 'Type': 'string'}]
                Partition Metadata: []           
    </context>""",
        'AI': """SELECT AVG(CAST(area AS DOUBLE))
FROM dataall_homes_11p3uu8f.listings
WHERE area IS NOT NULL;""",
    },
    {
        'User': """I want to get the average of the 3 most expensive listings with less than 3 bedrooms\\n\\nBased on on the following glue metadata: \n            
    <context>
    Database Name : dataall_homes_11p3uu8f
    Table name: listings 
                Column Metadata: [{'Name': 'price', 'Type': 'bigint'}, {'Name': 'area', 'Type': 'bigint'}, {'Name': 'bedrooms', 'Type': 'bigint'}, {'Name': 'bathrooms', 'Type': 'bigint'}, {'Name': 'stories', 'Type': 'bigint'}, {'Name': 'mainroad', 'Type': 'string'}, {'Name': 'guestroom', 'Type': 'string'}, {'Name': 'basement', 'Type': 'string'}, {'Name': 'hotwaterheating', 'Type': 'string'}, {'Name': 'airconditioning', 'Type': 'string'}, {'Name': 'parking', 'Type': 'bigint'}, {'Name': 'prefarea', 'Type': 'string'}, {'Name': 'furnishingstatus', 'Type': 'string'}, {'Name': 'passengerid', 'Type': 'bigint'}, {'Name': 'survived', 'Type': 'bigint'}, {'Name': 'pclass', 'Type': 'bigint'}, {'Name': 'name', 'Type': 'string'}, {'Name': 'sex', 'Type': 'string'}, {'Name': 'age', 'Type': 'double'}, {'Name': 'sibsp', 'Type': 'bigint'}, {'Name': 'parch', 'Type': 'bigint'}, {'Name': 'ticket', 'Type': 'string'}, {'Name': 'fare', 'Type': 'double'}, {'Name': 'cabin', 'Type': 'string'}, {'Name': 'embarked', 'Type': 'string'}]
                Partition Metadata: []
    <context/>""",
        'AI': """SELECT AVG(price) AS average_price
FROM (
  SELECT price
  FROM dataall_homes_11p3uu8f.listings
  WHERE bedrooms > 3
  ORDER BY price DESC
  LIMIT 3)""",
    },
    {
        'User': """I want to get the  3 least expensive listings with more than 3 bedrooms\n\nBased on on the following glue metadata: \n            
    <context>
    Database name : dataall_homes_11p3uu8f
    Table name: listings 
                Column Metadata: [{'Name': 'price', 'Type': 'bigint'}, {'Name': 'area', 'Type': 'bigint'}, {'Name': 'bedrooms', 'Type': 'bigint'}, {'Name': 'bathrooms', 'Type': 'bigint'}, {'Name': 'stories', 'Type': 'bigint'}, {'Name': 'mainroad', 'Type': 'string'}, {'Name': 'guestroom', 'Type': 'string'}, {'Name': 'basement', 'Type': 'string'}, {'Name': 'hotwaterheating', 'Type': 'string'}, {'Name': 'airconditioning', 'Type': 'string'}, {'Name': 'parking', 'Type': 'bigint'}, {'Name': 'prefarea', 'Type': 'string'}, {'Name': 'furnishingstatus', 'Type': 'string'}, {'Name': 'passengerid', 'Type': 'bigint'}, {'Name': 'survived', 'Type': 'bigint'}, {'Name': 'pclass', 'Type': 'bigint'}, {'Name': 'name', 'Type': 'string'}, {'Name': 'sex', 'Type': 'string'}, {'Name': 'age', 'Type': 'double'}, {'Name': 'sibsp', 'Type': 'bigint'}, {'Name': 'parch', 'Type': 'bigint'}, {'Name': 'ticket', 'Type': 'string'}, {'Name': 'fare', 'Type': 'double'}, {'Name': 'cabin', 'Type': 'string'}, {'Name': 'embarked', 'Type': 'string'}]
                Partition Metadata: []
        <context/>""",
        'AI': """SELECT *
FROM dataall_homes_11p3uu8f.listings
WHERE bedrooms > 3
ORDER BY price ASC
LIMIT 3;""",
    },
    {
        'User': """I want to see if any letter has been sent from 900 Somerville Avenue to 2 Finnigan Street what is the content n\nBased on on the following glue metadata: \n            
    <context>
    ["Database name: dataall_packages_omf768qq \n    Table name: packages \n    Column Metadata: [{'Name': 'id', 'Type': 'bigint'}, {'Name': 'contents', 'Type': 'string'}, {'Name': 'from_address_id', 'Type': 'bigint'}, {'Name': 'to_address_id', 'Type': 'bigint'}]\n    Partition Metadata: []\n    ", "\n    Table name: addresses \n    Column Metadata: [{'Name': 'id', 'Type': 'bigint'}, {'Name': 'address', 'Type': 'string'}, {'Name': 'type', 'Type': 'string'}]\n    Partition Metadata: []\n    ", "\n    Table name: drivers \n    Column Metadata: [{'Name': 'id', 'Type': 'bigint'}, {'Name': 'name', 'Type': 'string'}]\n    Partition Metadata: []\n    ", "\n    Table name: scans \n    Column Metadata: [{'Name': 'id', 'Type': 'bigint'}, {'Name': 'driver_id', 'Type': 'bigint'}, {'Name': 'package_id', 'Type': 'bigint'}, {'Name': 'address_id', 'Type': 'bigint'}, {'Name': 'action', 'Type': 'string'}, {'Name': 'timestamp', 'Type': 'string'}]\n    Partition Metadata: []\n    "]

    <context/>
        """,
        'AI': """SELECT p.contents
FROM dataall_packages_omf768qq.packages p
JOIN dataall_packages_omf768qq.addresses a1 ON p.from_address_id = a1.id
JOIN dataall_packages_omf768qq.addresses a2 ON p.to_address_id = a2.id
WHERE a1.address = '900 Somerville Avenue' AND a2.address = '2 Finnigan Street'""",
    },
]


class StructuredBedrockClient:
    def __init__(self, account_id: str, region: str):
        self.__session = SessionHelper.get_session()
        self._client = self.__session.client('bedrock-runtime', region_name=region)
        model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        model_kwargs = {
            'max_tokens': 2048,
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

    def invoke_model(self, prompt: str, metadata: str):
        # context = str(metadata)
        context = '\n'.join(metadata) if isinstance(metadata, list) else metadata

        messages = [
            (
                'system',
                """ You will be given the name of the gluedatabase, metadata from a glue table and a user prompt from a user. Based on this information.
        Your job is to turn the prompt into a SQL query that will be sent to query athena.

        Think step by step, take your time and take the following points into consideration Its crucial that you follow them:
        

        - I only want you to returned the SQL needed (NO EXPLANATION or anything else).

        - Tables are referenced on the following form 'database_name.table_name' IE 'Select * FROM database_name.table_name ...' (NOT 'SELECT * FROM table_name ...) since we dont have access to the table name directly since its not global vaiable.

        - Take relations between tables into consideration, for example if you have a table with columns that might reference the other tables, you would need to join them in the query.

        - Answer on the same form as the examples given below.

        - It should be read only

        Step 1: Determine if the given tables columns are suitable to answer the question.
        If not respond with "Error: The tables provided does not give enough information"

        Step 2: Determine if the user wants to perform any mutations, if so return "Error: Only read queries are allowed at the moment"

        Step 3: Determine if joins will be needed.

        Step 4: Generate the SQL in order to solve the problem.

                
            <examples>
            {examples}
            </examples>
        """,
            ),
            (
                'human',
                """{question}\n\nBased on on the following glue metadata: 
                <context>
                    {context}
                </context>
                
                """,
            ),
        ]

        prompts = ChatPromptTemplate.from_messages(messages)

        chain = prompts | self.__model | StrOutputParser()
        response = chain.invoke({'question': prompt, 'context': context, 'examples': examples})
        return response
