import { gql } from 'apollo-boost';

const createDataset = (input) => {
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation CreateDataset($input: NewDatasetInput) {
        createDataset(input: $input) {
          datasetUri
          label
          userRoleForDataset
        }
      }
    `
  };
};

export default createDataset;
