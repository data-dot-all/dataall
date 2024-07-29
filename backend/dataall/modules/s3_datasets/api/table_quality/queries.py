from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table_quality.resolvers import (
    list_table_data_quality_rules,
)

listTableDataQualityRules = gql.QueryField(
    name='listTableDataQualityRules',
    args=[
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))
    ],
    type=gql.Ref('TableDataQualityRulesSearchResult'), ## todo: define types
    resolver=list_table_data_quality_rules,
)