import { gql } from 'apollo-boost';

export const updateTopic = ({ input, topicUri }) => ({
  variables: {
    topicUri,
    input
  },
  mutation: gql`
    mutation UpdateTopic($topicUri: String, $input: OrganizationTopicInput) {
      updateTopic(organizationUri: $organizationUri, input: $input) {
        topicUri
        label
        description
        created
        owner
      }
    }
  `
});
