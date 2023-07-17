import { gql } from 'apollo-boost';

const updateEnvironmentStack = ({ environmentUri }) => ({
  variables: { environmentUri },
  mutation: gql`
    mutation updateEnvironmentStack($environmentUri: String!) {
      updateEnvironmentStack(environmentUri: $environmentUri)
    }
  `
});

export default updateEnvironmentStack;
