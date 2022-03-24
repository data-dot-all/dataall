import { gql } from 'apollo-boost';

const countUpVotes = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  query: gql`
        query countUpVotes($targetUri:String!, $targetType:String!){
            countUpVotes(targetUri:$targetUri, targetType:$targetType)
        }
        `
});

export default countUpVotes;
