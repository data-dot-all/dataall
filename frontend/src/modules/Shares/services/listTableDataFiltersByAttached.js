import { gql } from 'apollo-boost';

export const listTableDataFiltersByAttached = ({
  attachedDataFilterUri,
  filter
}) => ({
  variables: {
    attachedDataFilterUri,
    filter
  },
  query: gql`
    query listTableDataFiltersByAttached(
      $attachedDataFilterUri: String
      $filter: DatasetTableFilter
    ) {
      listTableDataFiltersByAttached(
        attachedDataFilterUri: $attachedDataFilterUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          filterUri
          label
          description
          filterType
          includedCols
          rowExpression
        }
      }
    }
  `
});
