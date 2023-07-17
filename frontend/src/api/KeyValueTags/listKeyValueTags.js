import { gql } from 'apollo-boost';

const listKeyValueTags = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  query: gql`
    query listKeyValueTags($targetUri: String!, $targetType: String!) {
      listKeyValueTags(targetUri: $targetUri, targetType: $targetType) {
        tagUri
        targetUri
        targetType
        key
        value
        cascade
      }
    }
  `
});

export default listKeyValueTags;
