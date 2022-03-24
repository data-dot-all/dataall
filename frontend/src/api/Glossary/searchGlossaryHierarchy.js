import { gql } from 'apollo-boost';

const searchGlossaryHierarchy = ({ filter, targetUri }) => ({
  variables: {
    filter,
    targetUri
  },
  query: gql`query SearchGlossaryHierarchy($filter:TermFilter, $targetUri:String){
            searchGlossaryHierarchy(filter:$filter){
                count
                page
                pages
                hasNext
                hasPrevious
                nodes{
                    __typename
                    ...on Glossary{
                        nodeUri
                        parentUri
                        label
                        readme
                        created
                        owner
                        path
                        isMatch
                    }
                    ...on Category{
                        nodeUri
                        parentUri
                        label
                        readme
                        created
                        owner
                        path
                        isMatch
                    }
                    ...on Term{
                        nodeUri
                        parentUri
                        label
                        readme
                        created
                        owner
                        path
                        isMatch
                        assetLink(targetUri:$targetUri){
                            nodeUri
                            targetUri
                            created
                            approvedByOwner
                            approvedBySteward
                        }
                    }
                }
            }
        }`
});

export default searchGlossaryHierarchy;
