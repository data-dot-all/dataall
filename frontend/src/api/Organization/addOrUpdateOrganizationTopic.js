import { gql } from 'apollo-boost';

const createTopic = ({ input, organizationUri }) => ({
  variables: {
    organizationUri,
    input
  },
  mutation: gql`mutation createTopic($organizationUri:String,$input:OrganizationTopicInput){
            createTopic(organizationUri:$organizationUri,input:$input){
                    topicUri
                    label
                    description
                    created
                    owner
                }
            }
        `
});

export default createTopic;
