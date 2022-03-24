import { gql } from 'apollo-boost';

const removeGroupFromEnvironment = ({ environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri
  },
  mutation: gql`mutation removeGroupFromEnvironment($environmentUri:String!,$groupUri:String!){
            removeGroupFromEnvironment(environmentUri:$environmentUri, groupUri:$groupUri){
              environmentUri
            }
        }`
});

export default removeGroupFromEnvironment;
