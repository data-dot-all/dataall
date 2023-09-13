import { gql } from 'apollo-boost';

export const createQuicksightDataSourceSet = ({ vpcConnectionId }) => ({
  variables: {
    vpcConnectionId
  },
  mutation: gql`
    mutation createQuicksightDataSourceSet($vpcConnectionId: String!) {
      createQuicksightDataSourceSet(vpcConnectionId: $vpcConnectionId)
    }
  `
});
