import { gql } from 'apollo-boost';

export const enableDataSubscriptions = ({ environmentUri, input }) => ({
  variables: {
    environmentUri,
    input
  },
  mutation: gql`
    mutation enableDataSubscriptions(
      $environmentUri: String!
      $input: EnableDataSubscriptionsInput
    ) {
      enableDataSubscriptions(environmentUri: $environmentUri, input: $input)
    }
  `
});
