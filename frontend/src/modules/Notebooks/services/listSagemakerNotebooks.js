import { gql } from 'apollo-boost';

export const listSagemakerNotebooks = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query ListSagemakerNotebooks($filter: SagemakerNotebookFilter) {
      listSagemakerNotebooks(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          notebookUri
          name
          owner
          description
          label
          created
          tags
          NotebookInstanceStatus
          userRoleForNotebook
          SamlAdminGroupName
          environment {
            label
            name
            environmentUri
            AwsAccountId
            region
          }
          organization {
            label
            name
            organizationUri
          }
          stack {
            stack
            status
          }
        }
      }
    }
  `
});
