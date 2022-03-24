import { gql } from 'apollo-boost';

const getShareAccessRequestFromLink = (linkid) => ({
  variables: { linkid },
  query: gql`query GetShareAccessRequestFromLink($linkid:String!){
        getShareAccessRequestFromLink(linkid:$linkid){
            shareUri
            description
            created
            owner
            principal{
                principalId
                principalType
                principalName
            }
        }
        }`
});

export default getShareAccessRequestFromLink;
