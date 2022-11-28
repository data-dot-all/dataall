import { gql } from 'apollo-boost';

const DisableDataSubscriptions = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  mutation: gql`
    mutation DisableDataSubscriptions($environmentUri: String!) {
      DisableDataSubscriptions(environmentUri: $environmentUri)
    }
  `
});

export default DisableDataSubscriptions;
