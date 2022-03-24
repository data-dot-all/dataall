import { gql } from 'apollo-boost';

const listFeedMessages = ({ targetUri, targetType, filter }) => ({
  variables: {
    targetUri,
    targetType,
    filter
  },
  query: gql`
            query GetFeed(
                $targetUri:String!,
                $targetType:String!,
                $filter:FeedMessageFilter
            ){
                getFeed(
                    targetUri:$targetUri,
                    targetType:$targetType
                ){
                    target{
                        __typename
                        ...on DatasetTable{
                            label
                        }
                        ... on Dataset {
                            label
                        }
                        ...on DatasetStorageLocation{
                            label
                        }
                        ...on Dashboard{
                            label
                        }
                        ...on Worksheet{
                            label
                        }
                        ...on SqlPipeline{
                            label
                        }
                    }
                    messages(filter:$filter){
                        count
                        hasNext
                        hasPrevious
                        page
                        pages
                        nodes{
                            content
                            feedMessageUri
                            creator
                            created
                        }
                    }

                }
            }
        `
});

export default listFeedMessages;
