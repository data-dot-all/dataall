import { gql } from 'apollo-boost';

const updateDataset = ({ datasetUri, input }) => {
  console.log('rcv', datasetUri, input);
  return {
    variables: {
      datasetUri,
      input
    },
    mutation: gql`mutation UpdateDataset($datasetUri:String,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                userRoleForDataset
            }
        }`
  };
};

export default updateDataset;
