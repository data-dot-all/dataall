import { gql } from 'apollo-boost';

const listUserActivities = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
            query ListUserActivities($filter:ActivityFilter){
                listUserActivities(filter:$filter){
                    count
                    page
                    pages
                    hasNext,
                    hasPrevious,
                    nodes{
                        activityUri
                        created
                        summary
                        targetUri
                        targetType
                        action
                    }
                }
            }`
});

export default listUserActivities;
