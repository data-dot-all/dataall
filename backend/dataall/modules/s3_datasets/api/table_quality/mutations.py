from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table_quality.input_types import (
    NewDataQualityRuleInput,
    UpdateDataQualityRuleInput, ## todo: define input_types
)
from dataall.modules.s3_datasets.api.table_quality.resolvers import (
    create_data_quality_rule,
    delete_data_quality_rule,
    update_data_quality_rule,
)## todo: define resolvers

createDataQualityRule = gql.MutationField(
    name='createDataQualityRule',
    args=[gql.Argument(name='input', type=gql.NonNullableType(NewDataQualityRuleInput))],
    type=gql.Ref('DataQualityRule'), ## todo: define types
    resolver=create_data_quality_rule,
)

updateDataQualityRule = gql.MutationField(
    name='updateDataQualityRule',
    args=[gql.Argument(name='input', type=gql.NonNullableType(UpdateDataQualityRuleInput))],
    type=gql.Ref('DataQualityRule'), ## todo: define types
    resolver=update_data_quality_rule,
)

deleteDataQualityRule = gql.MutationField(
    name='deleteDataQualityRule',
    args=[gql.Argument(name='ruleUri', type=gql.NonNullableType(gql.StringType))],
    type=gql.Boolean,
    resolver=delete_data_quality_rule,
)