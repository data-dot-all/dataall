import { gql } from 'apollo-boost';

export const getNetwork = (vpcUri) => ({
  variables: {
    vpcUri
  },
  query: gql`
    query getNetwork($vpcUri: String!) {
      getNetwork(vpcUri: $vpcUri) {
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
