import { gql } from 'apollo-boost';

export const getSagemakerNotebook = (notebookUri) => ({
  variables: {
    notebookUri
  },
  query: gql`
    query getSagemakerNotebook($notebookUri: String!) {
      getSagemakerNotebook(notebookUri: $notebookUri) {
        notebookUri
        name
        owner
        description
        label
        created
        tags
        NotebookInstanceStatus
        SamlAdminGroupName
        RoleArn
        VpcId
        SubnetId
        VolumeSizeInGB
        InstanceType
        environment {
          label
          name
          environmentUri
          AwsAccountId
          region
        }
        organization {
          label
          name
          organizationUri
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
      }
    }
  `
});
