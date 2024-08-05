from dataall.base.api.constants import GraphQLEnumMapper


def enum_resolver(context, source, enums_names):
    result = []
    for enum_class in GraphQLEnumMapper.__subclasses__():
        if enum_class.__name__ in enums_names:
            result.append(
                {
                    'name': enum_class.__name__,
                    'items': [{'name': item.name, 'value': str(item.value)} for item in enum_class],
                }
            )
    return result
