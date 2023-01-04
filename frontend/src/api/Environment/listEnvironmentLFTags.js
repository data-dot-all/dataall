import { gql } from 'apollo-boost';

const listEnvironmentLFTags = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query listEnvironmentLFTags(
      $environmentUri: String!
    ) {
      listEnvironmentLFTags(environmentUri: $environmentUri) {
        tagPermissionUri
        tagKey
        tagValues
      }
    }
  `
});

export default listEnvironmentLFTags;
