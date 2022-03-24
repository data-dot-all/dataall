import { gql } from 'apollo-boost';

const getSagemakerNotebookPresignedUrl = (notebookUri) => ({
  variables: {
    notebookUri
  },
  query: gql`
            query getSagemakerNotebookPresignedUrl ($notebookUri:String!){
                getSagemakerNotebookPresignedUrl(notebookUri:$notebookUri)
            }
        `
});

export default getSagemakerNotebookPresignedUrl;
