import { gql } from 'apollo-boost';

export const createMLStudioDomain = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createMLStudioDomain($input: NewStudioDomainInput) {
      createMLStudioDomain(input: $input) {
        vpcUri
        VpcId
        label
        description
        tags
        owner
        SamlGroupName
        privateSubnetIds
        privateSubnetIds
      }
    }
  `
});
