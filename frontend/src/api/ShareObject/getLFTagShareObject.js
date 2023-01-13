import { gql } from 'apollo-boost';

const getLFTagShareObject = ({ lftagShareUri }) => ({
  variables: {
    lftagShareUri
  },
  query: gql`
    query getLFTagShareObject($lftagShareUri: String!) {
      getLFTagShareObject(lftagShareUri: $lftagShareUri) {
        lftagShareUri
        lfTagKey
        lfTagValue
        created
        owner
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
  `
});

export default getLFTagShareObject;
