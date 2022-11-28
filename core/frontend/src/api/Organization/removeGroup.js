import { gql } from 'apollo-boost';

const removeGroupFromOrganization = ({ organizationUri, groupUri }) => ({
  variables: {
    organizationUri,
    groupUri
  },
  mutation: gql`
    mutation removeGroupFromOrganization(
      $organizationUri: String!
      $groupUri: String!
    ) {
      removeGroupFromOrganization(
        organizationUri: $organizationUri
        groupUri: $groupUri
      ) {
        organizationUri
      }
    }
  `
});

export default removeGroupFromOrganization;
