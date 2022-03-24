import { gql } from 'apollo-boost';

const checkEnvironment = (input) => ({
  variables: {
    input
  },
  query: gql`
            query CheckEnvironment($input:AwsEnvironmentInput!){
                checkEnvironment(input:$input)
            }
        `
});

export default checkEnvironment;
