import { gql } from 'apollo-boost';

export const disableDataSubscriptions = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  mutation: gql`
    mutation DisableDataSubscriptions($environmentUri: String!) {
      DisableDataSubscriptions(environmentUri: $environmentUri)
    }
  `
});
