import { gql } from 'apollo-boost';

const getEnumByName = ({ enum_name }) => ({
  variables: {
    enum_name
  },
  query: gql`
    query ${enum_name}{
      ${enum_name}{
          name
          value
      }
    }
  `
});

export const fetchEnum = async (client, enum_name) => {
  const response = await client.query(getEnumByName({ enum_name: enum_name }));
  if (!response.errors && response.data[enum_name] != null) {
    return response.data[enum_name];
  } else {
    return [];
  }
};
