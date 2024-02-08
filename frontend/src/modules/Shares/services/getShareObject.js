import { gql } from 'apollo-boost';

export const getShareObject = ({ shareUri, filter }) => ({
  variables: {
    shareUri,
    filter
  },
  query: gql`
    query getShareObject($shareUri: String!, $filter: ShareableObjectFilter) {
      getShareObject(shareUri: $shareUri) {
        shareUri
        created
        owner
        status
        requestPurpose
        rejectPurpose
        userRoleForShareObject
        consumptionData {
          s3AccessPointName
          sharedGlueDatabase
          s3bucketName
        }
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
        items(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            itemUri
            shareItemUri
            itemType
            itemName
            status
            action
            healthStatus
            healthMessage
            lastVerificationTime
          }
        }
        dataset {
          datasetUri
          datasetName
          SamlAdminGroupName
          environmentName
          AwsAccountId
          region
          exists
        }
      }
    }
  `
});
