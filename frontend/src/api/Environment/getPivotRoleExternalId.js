import { gql } from 'apollo-boost';

const getPivotRoleExternalId = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
            query getPivotRoleExternalId($organizationUri:String!){
                getPivotRoleExternalId(organizationUri:$organizationUri)
            }
        `
});

export default getPivotRoleExternalId;
