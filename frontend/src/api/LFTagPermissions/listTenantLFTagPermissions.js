import { gql } from 'apollo-boost';

const listTenantLFTagPermissions = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listTenantLFTagPermissions($filter: LFTagPermissionsFilter) {
      listTenantLFTagPermissions(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          tagPermissionUri
          SamlGroupName
          environmentUri
          environmentLabel
          awsAccount
          tagKey
          tagValues
        }
      }
    }
  `
});

export default listTenantLFTagPermissions;
