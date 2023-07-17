import gql from 'graphql-tag';

const listEnvironments = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query ListEnvironments($filter: EnvironmentFilter) {
      listEnvironments(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          environmentUri
          userRoleInEnvironment
          name
          label
          description
          AwsAccountId
          region
          created
          owner
          tags
          SamlGroupName
          EnvironmentDefaultIAMRoleName
          networks {
            VpcId
            privateSubnetIds
            publicSubnetIds
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
          organization {
            organizationUri
            name
            label
          }
        }
      }
    }
  `
});

export default listEnvironments;
