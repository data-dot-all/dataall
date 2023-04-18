import { gql } from 'apollo-boost';

export const createTopic = ({ input, organizationUri }) => ({
  variables: {
    organizationUri,
    input
  },
  mutation: gql`
    mutation createTopic(
      $organizationUri: String
      $input: OrganizationTopicInput
    ) {
      createTopic(organizationUri: $organizationUri, input: $input) {
        topicUri
        label
        description
        created
        owner
      }
    }
  `
});
