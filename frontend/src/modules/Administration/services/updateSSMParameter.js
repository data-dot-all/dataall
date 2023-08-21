import { gql } from 'apollo-boost';

export const updateSSMParameter = ({ name, value }) => ({
  variables: {
    name,
    value
  },
  mutation: gql`
    mutation updateSSMParameter($name: String!, $value: String!) {
      updateSSMParameter(name: $name, value: $value)
    }
  `
});
