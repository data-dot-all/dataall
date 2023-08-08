import { gql } from 'apollo-boost';

export const updateEnvironmentStack = ({ environmentUri }) => ({
  variables: { environmentUri },
  mutation: gql`
    mutation updateEnvironmentStack($environmentUri: String!) {
      updateEnvironmentStack(environmentUri: $environmentUri)
    }
  `
});
