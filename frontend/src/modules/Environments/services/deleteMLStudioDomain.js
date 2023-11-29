import { gql } from 'apollo-boost';

export const deleteMLStudioDomain = ({ sagemakerStudioUri }) => ({
  variables: {
    sagemakerStudioUri
  },
  mutation: gql`
    mutation deleteMLStudioDomain($sagemakerStudioUri: String!) {
      deleteMLStudioDomain(sagemakerStudioUri: $sagemakerStudioUri)
    }
  `
});
