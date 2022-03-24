import { gql } from 'apollo-boost';

const getSqlPipeline = (sqlPipelineUri) => ({
  variables: {
    sqlPipelineUri
  },
  query: gql`
            query GetSqlPipeline($sqlPipelineUri:String!){
                getSqlPipeline(sqlPipelineUri:$sqlPipelineUri){
                    sqlPipelineUri
                    name
                    owner
                    SamlGroupName
                    description
                    label
                    created
                    userRoleForPipeline
                    tags
                    repo
                    cloneUrlHttp
                    environment{
                        environmentUri
                        AwsAccountId
                        region
                        label
                    }
                    organization{
                        organizationUri
                        label
                        name
                    }
                    stack{
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
                    runs{
                        Id
                        StartedOn
                        JobRunState
                    }
                }
            }
        `
});

export default getSqlPipeline;
