from typing import List, Optional
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel


class MetadataOutput(BaseModel):
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    label: Optional[str] = None
    topics: Optional[List[str]] = None


class DatasetMetadataGenerationService:
    @staticmethod
    def get_dataset_prompt_template() -> PromptTemplate:
        prompt_template = """
              Generate or improve metadata for a dataset using the following provided data:
                - Dataset name: {label}
                - Current dataset description: {description}
                - Current tags for dataset: {tags}
                - Table names in the dataset: {table_names}
                - Folder names in the dataset: {folder_names}
                **Important**: 
                    - If the data indicates "No description provided" or is None or [] do not use that particular input for generating metadata.
                    - Only focus on generating the following metadata types as specified by the user: {metadata_types}. Do not include any other metadata types.
                    - Return the result as a Python dictionary.
                Your response should strictly contain the requested metadata types. Don't use ' ' in your response, use " ".
                For example, if the requested metadata types are "tags" and "description", the response should be:
                    "tags":<tags>
                    "description":<description>
                Evaluate if the given parameters are sufficient for generating the requested metadata, if not, respond with listing table names and folder names for description and for label keep the current name
                For tags and topics, ensure the output is a string list.  Label is singular so you should return only one label as string. 
                Return the result as a Python dictionary where the keys are the requested metadata types, all the keys must be lowercase and the values are the corresponding generated metadata.

            """
        return PromptTemplate.from_template(prompt_template)

    @staticmethod
    def format_dataset_prompt_template(
        template: PromptTemplate,
        metadata_types: List[str],
        label: str,
        description: str,
        tags: List[str],
        table_labels: List[str],
        table_descriptions: List[str],
        folder_labels: List[str],
    ) -> str:
        # TODO: add table description
        # TODO add input validation
        return template.format(
            label=label,
            description=description,
            tags=tags,
            table_names=table_labels,
            folder_names=folder_labels,
            metadata_types=metadata_types,
        )

    @staticmethod
    def get_table_prompt_template() -> PromptTemplate:
        prompt_template = """
                 Generate or improve metadata for a common_data['label'] table using the following provided data:
                    - Table name: {label}
                    - Current table description: {description}
                    - Current tags for table: {tags}
                    - Column names: {columns}
                    - Column Descriptions: {column_descriptions}
                    - (Only Input) Sample data: {sample_data}
                    **Important**: 
                    - If the data indicates "No description provided," do not use that particular input for generating metadata, these data is optional you should still generate in that case.
                    - Only focus on generating the following metadata types as specified by the user: {metadata_types}. Do not include any other metadata types.
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
        return PromptTemplate.from_template(prompt_template)

    @staticmethod
    def format_table_prompt_template(
        template: PromptTemplate,
        metadata_types: List[str],
        label: str,
        description: str,
        tags: List[str],
        column_names: List[str],
        column_descriptions: List[str],
        sample_data=None,
    ) -> str:
        # TODO add input validation
        return template.format(
            metadata_types=metadata_types,
            label=label,
            description=description,
            tags=tags,
            column_names=column_names,
            column_descriptions=column_descriptions,
            sample_data=sample_data,
        )

    @staticmethod
    def get_folder_prompt_template() -> PromptTemplate:
        prompt_template = """
                  Generate a detailed metadata description for a database table using following provided data: 
                  - folder name: {label}, 
                  - folder_description: {description}
                  - folder_tags: {tags}
                  - file names: {file_names} 
                    **Important**: 
                        - If the data indicates "No description provided," do not use that particular input for generating metadata.
                        - Only focus on generating the following metadata types as specified by the user: {metadata_types}. Do not include any other metadata types.
                        - Return the result as a Python dictionary.
                  Your response should strictly contain the requested metadata types.
                  For example, if the requested metadata types are "tags" and "description", the response should be:
                      "tags":<tags>
                      "description":<description>   
                  For tags and topics, ensure the output is a string list. Label is singular so you should return only one label as string.
                  Return a python dictionary, all the keys must be lowercase. Don't use ' ' in your response, use " ".   Include file types as pdf, and write file names in description.
                  Evaluate if the given parameters are sufficient for generating the requested metadata, if not, respond with "NotEnoughData" for all values of dictionary keys.
                """
        return PromptTemplate.from_template(prompt_template)

    @staticmethod
    def format_folder_prompt_template(
        template: PromptTemplate,
        metadata_types: List[str],
        label: str,
        description: str,
        tags: List[str],
        file_names: List[str],
    ) -> str:
        # TODO add input validation
        return template.format(
            label=label, description=description, tags=tags, metadata_types=metadata_types, file_names=file_names
        )
