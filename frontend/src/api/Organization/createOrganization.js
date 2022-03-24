import { gql } from 'apollo-boost';

const createOrganization = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation CreateOrg($input:NewOrganizationInput){
            createOrganization(input:$input){
                organizationUri
                label
                created
            }
        }`
});

export default createOrganization;
