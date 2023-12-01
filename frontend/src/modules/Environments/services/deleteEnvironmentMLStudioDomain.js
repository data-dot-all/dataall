import { gql } from 'apollo-boost';

export const deleteEnvironmentMLStudioDomain = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  mutation: gql`
    mutation deleteEnvironmentMLStudioDomain($environmentUri: String!) {
      deleteEnvironmentMLStudioDomain(environmentUri: $environmentUri)
    }
  `
});
