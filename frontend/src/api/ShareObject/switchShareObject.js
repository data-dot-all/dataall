import { gql } from 'apollo-boost';

const switchShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`mutation SwitchShareObject($shareUri:String!){
            switchShareObject(shareUri:$shareUri)
        }`
});

export default switchShareObject;
