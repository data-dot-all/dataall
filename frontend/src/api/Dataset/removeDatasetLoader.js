import { gql } from 'apollo-boost';

export const removeDatasetLoader = ({ loaderUri }) => ({
  variables: { loaderUri },
  mutation: gql`
    mutation RemoveDatasetLoader($loaderUri: String) {
      removeDatasetLoader(loaderUri: $loaderUri)
    }
  `
});
