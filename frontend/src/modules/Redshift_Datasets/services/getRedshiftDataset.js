import { gql } from 'apollo-boost';

export const getRedshiftDataset = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query getRedshiftDataset($datasetUri: String!) {
      getRedshiftDataset(datasetUri: $datasetUri) {
        datasetUri
        owner
        description
        label
        name
        region
        created
        imported
        userRoleForDataset
        SamlAdminGroupName
        AwsAccountId
        tags
        stewards
        topics
        confidentiality
        autoApprovalEnabled
        terms {
          count
          nodes {
            __typename
            ... on Term {
              nodeUri
              path
              label
            }
          }
        }
        environment {
          environmentUri
          label
          region
          organization {
            organizationUri
            label
          }
        }
        upvotes
        connection {
          connectionUri
          label
          redshiftType
          clusterId
          nameSpaceId
          workgroup
          redshiftUser
          secretArn
          database
        }
        schema
      }
    }
  `
});
