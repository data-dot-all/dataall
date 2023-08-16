from dataall.base.api.gql import String, Number, Boolean, Date


def test_basic():
    assert String.name == 'String'
    assert String.gql() == 'String'
    assert Number.name == 'Number'
    assert Number.gql() == 'Number'
    assert Boolean.name == 'Boolean'
    assert Boolean.gql() == 'Boolean'
    assert Date.name == 'Date'
    assert Date.gql() == 'Date'
