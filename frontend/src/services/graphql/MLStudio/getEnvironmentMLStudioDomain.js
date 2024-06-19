import { gql } from 'apollo-boost';

export const getEnvironmentMLStudioDomain = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query getEnvironmentMLStudioDomain($environmentUri: String!) {
      getEnvironmentMLStudioDomain(environmentUri: $environmentUri) {
        sagemakerStudioUri
        environmentUri
        label
        sagemakerStudioDomainName
        DefaultDomainRoleName
        vpcType
        vpcId
        subnetIds
        owner
        created
      }
    }
  `
});
