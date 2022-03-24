import { gql } from 'apollo-boost';

const importDataset = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation ImportDataset($input:ImportDatasetInput){
            importDataset(input:$input){
                datasetUri
                label
                userRoleForDataset
            }
        }`
});

export default importDataset;
