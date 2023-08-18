import { gql } from 'apollo-boost';

export const getOrganization = (organizationUri) => ({
  variables: { organizationUri },
  query: gql`
    query GetOrganization($organizationUri: String!) {
      getOrganization(organizationUri: $organizationUri) {
        organizationUri
        label
        tags
        SamlGroupName
        owner
        created
        description
        userRoleInOrganization
        stats {
          environments
          groups
        }
      }
    }
  `
});
