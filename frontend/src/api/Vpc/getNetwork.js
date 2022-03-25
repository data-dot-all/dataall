import { gql } from 'apollo-boost';

const getNetwork = (vpcUri) => ({
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

export default getNetwork;
