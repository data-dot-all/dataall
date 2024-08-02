import { gql } from 'apollo-boost';

export const listRedshiftConnectionSchemas = ({ connectionUri }) => ({
  variables: {
    connectionUri
  },
  query: gql`
    query listRedshiftConnectionSchemas($connectionUri: String!) {
      listRedshiftConnectionSchemas(connectionUri: $connectionUri)
    }
  `
});
