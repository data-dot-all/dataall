import { gql } from 'apollo-boost';

export const getEnvironment = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query GetEnvironment($environmentUri: String) {
      getEnvironment(environmentUri: $environmentUri) {
        environmentUri
        created
        userRoleInEnvironment
        description
        name
        label
        AwsAccountId
        dashboardsEnabled
        mlStudiosEnabled
        pipelinesEnabled
        warehousesEnabled
        region
        owner
        tags
        SamlGroupName
        EnvironmentDefaultBucketName
        EnvironmentDefaultIAMRoleArn
        EnvironmentDefaultIAMRoleName
        EnvironmentDefaultIAMRoleImported
        resourcePrefix
        subscriptionsEnabled
        subscriptionsProducersTopicImported
        subscriptionsConsumersTopicImported
        subscriptionsConsumersTopicName
        subscriptionsProducersTopicName
        organization {
          organizationUri
          label
          name
        }
        stack {
          stack
          status
          stackUri
          targetUri
          accountid
          region
          stackid
          link
          outputs
          resources
        }
        dashboardsEnabled
        mlStudiosEnabled
        pipelinesEnabled
        warehousesEnabled
        networks {
          VpcId
          privateSubnetIds
          publicSubnetIds
        }
        parameters {
          key
          value
        }
      }
    }
  `
});
