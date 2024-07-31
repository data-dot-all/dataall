import { gql } from 'apollo-boost';

const getEnumByName = ({ enum_names }) => ({
  variables: {
    enum_names: enum_names
  },
  query: gql`
    query queryEnums($enum_names: [String]) {
      queryEnums(enums_names: $enum_names) {
        name
        items {
          name
          value
        }
      }
    }
  `
});

/// function to fetch multiple enums
/// output -- dictionary
// {
//  'enumName': [{name: '...', value: '..'}]
// }
export const fetchEnums = async (client, enum_names) => {
  const response = await client.query(
    getEnumByName({ enum_names: enum_names })
  );
  let enum_dict = {};
  if (!response.errors && response.data.queryEnums != null) {
    response.data.queryEnums.map((x) => {
      enum_dict[x.name] = x.items;
    });
  }
  return enum_dict;
};
