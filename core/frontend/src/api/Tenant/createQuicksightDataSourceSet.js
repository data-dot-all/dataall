import { gql } from 'apollo-boost';

const createQuicksightDataSourceSet = ({vpcConnectionId}) => ({
  variables: {
    vpcConnectionId
  },
  mutation: gql`
    mutation createQuicksightDataSourceSet ($vpcConnectionId: String!) {
      createQuicksightDataSourceSet(vpcConnectionId: $vpcConnectionId)
    }
  `
});

export default createQuicksightDataSourceSet;
