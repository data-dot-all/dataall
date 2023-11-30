import { gql } from 'apollo-boost';

export const createMLStudioDomain = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createMLStudioDomain($input: NewStudioDomainInput) {
      createMLStudioDomain(input: $input) {
        sagemakerStudioUri
        environmentUri
        label
        vpcType
        vpcId
        subnetIds
      }
    }
  `
});
