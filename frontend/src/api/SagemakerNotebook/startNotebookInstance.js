import { gql } from 'apollo-boost';

const startSagemakerNotebook = (notebookUri) => ({
  variables: {
    notebookUri
  },
  mutation: gql`
            mutation StartSagemakerNotebook($notebookUri:String!){
                startSagemakerNotebook(notebookUri:$notebookUri)
            }
        `
});

export default startSagemakerNotebook;
