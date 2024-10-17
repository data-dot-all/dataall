SQL_EXAMPLES = [
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

TEXT_TO_SQL_PROMPT_TEMPLATE = """
You will be given the name of an AWS Glue Database, metadata from one or more AWS Glue Table(s) and a user prompt from a user. 

Based on this information your job is to turn the prompt into a SQL query that will be sent to query the data within the tables in Amazon Athena.

Take the following points into consideration. It is crucial that you follow them:

- I only want you to returned the SQL needed (NO EXPLANATION or anything else).

- Tables are referenced on the following form 'database_name.table_name' (for example 'Select * FROM database_name.table_name ...' and not 'SELECT * FROM table_name ...) since we dont have access to the table name directly since its not global vaiable.

- Take relations between tables into consideration, for example if you have a table with columns that might reference the other tables, you would need to join them in the query.

- The generate SQL statement MUST be Read only (no WRITE, INSERT, ALTER or DELETE keywords)

- Answer on the same form as the examples given below.

Examples:
{examples}


I want you to follow the following steps when generating the SQL statement: 

Step 1: Determine if the given tables columns are suitable to answer the question.
If not respond with "Error: The tables provided does not give enough information"

Step 2: Determine if the user wants to perform any mutations, if so return "Error: Only READ queries are allowed"

Step 3: Determine if joins will be needed.

Step 4: Generate the SQL in order to solve the problem.


Based on the following glue metadata: 
<context>
{context}
</context>

User prompt: {prompt}


"""


PROCESS_TEXT_PROMPT_TEMPLATE = """
You are an AI assistant tasked with analyzing and processing text content. Your goal is to provide accurate and helpful responses based on the given content and user prompt. 
You'll be given content to analyze and a prompt from the user based on the information in the document I want you to follow the following steps:

1. Detetermine if the document has the information to be able to answer the question. If not respond with "Error: The Document does not provide the information needed to answer you question"
2. I want you to answer the question based on the information in the document.
3. At the bottom I want you to provide the sources (the parts of the document where you found the results). The sources should be listed in order


Content to analyze:
{content}

User prompt: {prompt}

Please provide a response that addresses the user's prompt in the context of the given content. Be thorough, accurate, and helpful in your analysis.
"""
