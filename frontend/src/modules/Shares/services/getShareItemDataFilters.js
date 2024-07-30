import { gql } from 'apollo-boost';

export const getShareItemDataFilters = ({ attachedDataFilterUri }) => ({
  variables: {
    attachedDataFilterUri
  },
  query: gql`
    query getShareItemDataFilters($attachedDataFilterUri: String!) {
      getShareItemDataFilters(attachedDataFilterUri: $attachedDataFilterUri) {
        attachedDataFilterUri
        label
        dataFilterUris
        dataFilterNames
        itemUri
      }
    }
  `
});
