import { gql } from 'apollo-boost';

const searchInbox = ({ filter }) => ({
  variables: { filter },
  query: gql`query RequestsToMe($filter:ShareObjectFilter){
            requestsToMe(filter:$filter){
                count
                page
                pages
                hasNext
                hasPrevious
                nodes{
                    owner
                    created
                    deleted
                    shareUri
                    status
                    userRoleForShareObject
                    principal{
                        principalId
                        principalType
                        principalName
                        AwsAccountId
                        region
                    }
                    statistics{
                        tables
                        locations
                    }
                    dataset{
                        datasetUri
                        datasetName
                        datasetOrganizationName
                        datasetOrganizationUri
                    }
                }


            }
        }`
});

export default searchInbox;
