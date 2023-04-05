import { gql } from 'apollo-boost';

export const listDatasetLoaders = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
    query GetDataset($filter: DatasetLoaderFilter, $datasetUri: String!) {
      getDataset(datasetUri: $datasetUri) {
        datasetUri
        loaders(filter: $filter) {
          count
          page
          pageSize
          hasNext
          hasPrevious
          pages
          nodes {
            loaderUri
            description
            label
            IAMPrincipalArn
            description
            label
            tags
          }
        }
      }
    }
  `
});
