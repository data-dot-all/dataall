import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';

export const useGroups = () => {
  const dispatch = useDispatch();
  const [groups, setGroups] = useState(null);
  const fetchGroups = async () => {
    if (
      !process.env.REACT_APP_COGNITO_USER_POOL_ID &&
      process.env.REACT_APP_GRAPHQL_API.includes('localhost')
    ) {
      setGroups(['Engineers', 'Scientists']);
    } else {
      const session = await Auth.currentSession();
      const cognitoGroups = session.getIdToken().payload['cognito:groups'];
      const samlGroups = session.getIdToken().payload['custom:saml.groups'] // nosemgrep
        ? session // nosemgrep
            .getIdToken() // nosemgrep
            .payload['custom:saml.groups'].replace('[', '') // nosemgrep
            .replace(']', '') // nosemgrep
            .replace(/, /g, ',') // nosemgrep
            .split(',') // nosemgrep
        : [];
      setGroups([].concat(cognitoGroups).concat(samlGroups).filter(Boolean));
    }
  };

  useEffect(() => {
    if (!groups) {
      fetchGroups().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  });

  return groups;
};
