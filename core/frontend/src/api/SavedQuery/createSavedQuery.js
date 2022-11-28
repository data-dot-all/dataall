import { gql } from 'apollo-boost';

const createSavedQuery = ({ scheduledQueryUri, input }) => ({
  variables: {
    scheduledQueryUri,
    input
  },
  mutation: gql`
    mutation CreateSavedQuery(
      $scheduledQueryUri: String!
      $input: NewSavedQueryInput
    ) {
      createSavedQuery(scheduledQueryUri: $scheduledQueryUri, input: $input) {
        savedQueryUri
        name
        label
        created
        description
        tags
      }
    }
  `
});

export default createSavedQuery;
