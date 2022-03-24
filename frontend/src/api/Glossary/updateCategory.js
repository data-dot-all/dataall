import { gql } from 'apollo-boost';

const updateCategory = ({ input, nodeUri }) => ({
  variables: {
    input,
    nodeUri
  },
  mutation: gql`mutation UpdateCategory($nodeUri:String!,$input:UpdateCategoryInput){
            updateCategory(nodeUri:$nodeUri, input:$input){
                nodeUri
                label
                path
                readme
                created
                owner
            }
        }`
});

export default updateCategory;
