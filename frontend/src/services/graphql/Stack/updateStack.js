import { gql } from 'apollo-boost';

export const updateStack = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  mutation: gql`
    mutation updateStack($targetUri: String!, $targetType: String!) {
      updateStack(targetUri: $targetUri, targetType: $targetType) {
        stackUri
        targetUri
        name
      }
    }
  `
});
