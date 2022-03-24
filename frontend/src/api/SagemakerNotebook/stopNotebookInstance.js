import { gql } from 'apollo-boost';

const stopSagemakerNotebook = (notebookUri) => ({
  variables: {
    notebookUri
  },
  mutation: gql`
            mutation StopSagemakerNotebook($notebookUri:String!){
                stopSagemakerNotebook(notebookUri:$notebookUri)
            }
        `
});

export default stopSagemakerNotebook;
