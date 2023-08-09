import { gql } from 'apollo-boost';

export const deleteNetwork = ({ vpcUri }) => ({
  variables: {
    vpcUri
  },
  mutation: gql`
    mutation deleteNetwork($vpcUri: String!) {
      deleteNetwork(vpcUri: $vpcUri)
    }
  `
});
