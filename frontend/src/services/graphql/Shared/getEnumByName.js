import { gql } from 'apollo-boost';

const getEnumByName = ({ enum_names }) => ({
  variables: {
    enum_names: enum_names
  },
  query: gql`
    query queryEnum($enum_names: [String]) {
      queryEnum(enums_names: $enum_names) {
        name
        items {
          name
          value
        }
      }
    }
  `
});

export const fetchOneEnum = async (client, enum_name) => {
  const response = await client.query(
    getEnumByName({ enum_names: [enum_name] })
  );
  if (!response.errors && response.data.queryEnum != null) {
    return response.data.queryEnum[0].items;
  } else {
    return [];
  }
};

export const fetchEnums = async (client, enum_names) => {
  const response = await client.query(
    getEnumByName({ enum_names: enum_names })
  );
  let result = {};
  if (!response.errors && response.data.queryEnum != null) {
    for (let i = 0; i < response.data.queryEnum.length; i++) {
      result[response.data.queryEnum[i].name] =
        response.data.queryEnum[i].items;
    }
  } else {
    return result;
  }
};
