import { gql } from 'apollo-boost';

const searchSqlPipelines = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query ListSqlPipelines($filter: SqlPipelineFilter) {
      listSqlPipelines(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          sqlPipelineUri
          name
          owner
          SamlGroupName
          description
          label
          created
          tags
          organization {
            organizationUri
            label
            name
          }
          environment {
            environmentUri
            AwsAccountId
            region
            label
          }
          userRoleForPipeline
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
    }
  `
});

export default searchSqlPipelines;
