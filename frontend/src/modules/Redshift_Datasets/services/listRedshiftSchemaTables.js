import { gql } from 'apollo-boost';

export const listRedshiftSchemaTables = ({ connectionUri, schema }) => ({
  variables: {
    connectionUri,
    schema
  },
  query: gql`
    query listRedshiftSchemaTables($connectionUri: String!, $schema: String!) {
      listRedshiftSchemaTables(connectionUri: $connectionUri, schema: $schema) {
        name
        type
      }
    }
  `
});
