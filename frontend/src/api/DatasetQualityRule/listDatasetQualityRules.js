import { gql } from 'apollo-boost';

const listDatasetQualityRules = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri, filter
  },
  query: gql`
            query ListDatasetQualityRules($datasetUri:String!,$filter:DatasetQualityRuleFilter){
                listDatasetQualityRules(datasetUri:$datasetUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        ruleUri
                        name
                        label
                        description
                        created
                        query
                    }

                }
            }
        `
});

export default listDatasetQualityRules;
