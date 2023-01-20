import { gql } from 'apollo-boost';

const getLFTagShareRequestsToMe = ({ filter }) => ({
  variables: { filter },
  query: gql`
    query getLFTagShareRequestsToMe($filter: ShareObjectFilter) {
      getLFTagShareRequestsToMe(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          owner
          created
          deleted
          lftagShareUri
          lfTagKey
          lfTagValue
          status
          userRoleForShareObject
          principal {
            principalId
            principalType
            principalName
            principalIAMRoleName
            SamlGroupName
            environmentUri
            environmentName
            AwsAccountId
            region
            organizationUri
            organizationName
          }
        }
      }
    }
  `
});

export default getLFTagShareRequestsToMe;
