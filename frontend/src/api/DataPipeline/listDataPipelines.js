import { gql } from 'apollo-boost';

const searchDataPipelines = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query ListDataPipelines($filter: DataPipelineFilter) {
      listDataPipelines(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          DataPipelineUri
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

export default searchDataPipelines;
