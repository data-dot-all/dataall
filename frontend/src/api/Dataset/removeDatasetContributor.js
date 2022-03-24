import { gql } from 'apollo-boost';

const removeDatasetContributor = ({ userName, datasetUri }) => ({
  variables: { userName, datasetUri },
  mutation: gql`mutation RemoveDatasetContributor(
            $datasetUri:String,
            $userName:String
        ){
            removeDatasetContributor(
                datasetUri:$datasetUri,
                userName:$userName
            ){
                datasetUri
                label
                userRoleForDataset
            }
        }`
});

export default removeDatasetContributor;
