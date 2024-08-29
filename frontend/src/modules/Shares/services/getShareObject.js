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
        canViewLogs
        principal {
          principalName
          principalType
          principalId
          principalRoleName
          SamlGroupName
          environmentName
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
            attachedDataFilterUri
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
          description
          datasetType
        }
      }
    }
  `
});
