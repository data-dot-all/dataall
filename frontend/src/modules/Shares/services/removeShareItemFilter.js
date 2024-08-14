import { gql } from 'apollo-boost';

export const removeShareItemFilter = ({ attachedDataFilterUri }) => {
  return {
    variables: {
      attachedDataFilterUri
    },
    mutation: gql`
      mutation removeShareItemFilter($attachedDataFilterUri: String!) {
        removeShareItemFilter(attachedDataFilterUri: $attachedDataFilterUri)
      }
    `
  };
};
