import { gql } from 'apollo-boost';

export const archiveOrganization = (organizationUri) => ({
  variables: {
    organizationUri
  },
  mutation: gql`
    mutation ArciveOrg($organizationUri: String!) {
      archiveOrganization(organizationUri: $organizationUri)
    }
  `
});
