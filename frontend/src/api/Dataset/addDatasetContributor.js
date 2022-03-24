import { gql } from 'apollo-boost';

const addDatasetContributor = ({ userName, datasetUri, role }) => ({
  variables: { userName, datasetUri, role },
  mutation: gql`mutation AddDatasetContributor(
            $datasetUri:String,
            $userName:String,
            $role:DatasetRole
        ){
            addDatasetContributor(
                datasetUri:$datasetUri,
                userName:$userName,
                role : $role
            ){
                datasetUri
                label
                userRoleForDataset
            }
        }`
});

export default addDatasetContributor;
