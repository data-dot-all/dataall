import { gql } from 'apollo-boost';

export const checkEnvironment = (input) => ({
  variables: {
    input
  },
  query: gql`
    query CheckEnvironment($input: AwsEnvironmentInput!) {
      checkEnvironment(input: $input)
    }
  `
});
