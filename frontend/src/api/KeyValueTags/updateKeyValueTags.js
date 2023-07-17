import { gql } from 'apollo-boost';

const updateKeyValueTags = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateKeyValueTags($input: UpdateKeyValueTagsInput!) {
      updateKeyValueTags(input: $input) {
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

export default updateKeyValueTags;
