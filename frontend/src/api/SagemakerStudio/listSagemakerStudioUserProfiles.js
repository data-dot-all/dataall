import { gql } from 'apollo-boost';

const listSagemakerStudioUserProfiles = (filter) => ({
  variables: {
    filter
  },
  query: gql`
            query listSagemakerStudioUserProfiles($filter:SagemakerStudioUserProfileFilter){
                listSagemakerStudioUserProfiles(filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        sagemakerStudioUserProfileUri
                        name
                        owner
                        description
                        label
                        created
                        tags
                        sagemakerStudioUserProfileStatus
                        userRoleForSagemakerStudioUserProfile
                        environment{
                            label
                            name
                            environmentUri
                            AwsAccountId
                            region
                            SamlGroupName
                        }
                        organization{
                            label
                            name
                            organizationUri
                        }
                        stack{
                            stack
                            status
                        }
                    }

                }
            }
        `
});

export default listSagemakerStudioUserProfiles;
