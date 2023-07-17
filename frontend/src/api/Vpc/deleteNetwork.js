import { gql } from 'apollo-boost';

const deleteNetwork = ({ vpcUri }) => ({
  variables: {
    vpcUri
  },
  mutation: gql`
    mutation deleteNetwork($vpcUri: String!) {
      deleteNetwork(vpcUri: $vpcUri)
    }
  `
});

export default deleteNetwork;
