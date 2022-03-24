import { gql } from 'apollo-boost';

const createTerm = ({ input, parentUri }) => ({
  variables: {
    input,
    parentUri
  },
  mutation: gql`mutation CreateTerm($parentUri:String!,$input:CreateTermInput){
            createTerm(parentUri:$parentUri, input:$input){
                nodeUri
                label
                path
                readme
                created
                owner
            }
        }`
});

export default createTerm;
