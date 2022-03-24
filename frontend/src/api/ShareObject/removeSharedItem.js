import { gql } from 'apollo-boost';

const removeSharedItem = ({ shareItemUri }) => ({
  variables: {
    shareItemUri
  },
  mutation: gql`mutation RemoveSharedItem($shareItemUri:String!){
            removeSharedItem(shareItemUri:$shareItemUri)
        }`
});

export default removeSharedItem;
