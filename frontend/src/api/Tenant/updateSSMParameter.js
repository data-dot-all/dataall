import { gql } from 'apollo-boost';

const updateSSMParameter = ({ name, value }) => ({
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

export default updateSSMParameter;
