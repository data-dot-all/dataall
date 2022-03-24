import { gql } from 'apollo-boost';

const createSagemakerNotebook = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation CreateSagemakerNotebook(
            $input:NewSagemakerNotebookInput,
        ){
            createSagemakerNotebook(input:$input){
                notebookUri
                name
                label
                created
                description
                tags
            }
        }`
});

export default createSagemakerNotebook;
