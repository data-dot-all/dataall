import { gql } from 'apollo-boost';

const deleteTerm = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`mutation deleteTerm($nodeUri: String!){
            deleteTerm(nodeUri:$nodeUri)
        }`
});

export default deleteTerm;
