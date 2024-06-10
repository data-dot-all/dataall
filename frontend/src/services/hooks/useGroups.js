import { Auth } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, getGroupsForUser } from 'services';
import { useAuth } from 'authentication';

export const useGroups = () => {
  const dispatch = useDispatch();
  const [groups, setGroups] = useState(null);
  const client = useClient();
  const auth = useAuth();
  const fetchGroups = async () => {
    if (
      !process.env.REACT_APP_COGNITO_USER_POOL_ID &&
      process.env.REACT_APP_GRAPHQL_API.includes('localhost')
    ) {
      setGroups(['Engineers', 'Scientists', 'DAAdministrators']);
    } else if (process.env.REACT_APP_CUSTOM_AUTH) {
      // Returning when auth.user is not present
      // Not dispatching error as useGroups is triggered in auth guard when the user is not authenticated
      if (!auth.user) return;
      // return if the client is null, and then trigger this when the client is present
      if (client == null) return;
      const response = await client.query(getGroupsForUser(auth.user.short_id));
      if (!response.error) {
        setGroups(response.data.getGroupsForUser);
      } else {
        dispatch({ type: SET_ERROR, error: response.error });
      }
    } else {
      const session = await Auth.currentSession();
      const cognitoGroups = session.getIdToken().payload['cognito:groups'];
      const samlGroups = session.getIdToken().payload['custom:saml.groups']
        ? session
            .getIdToken()
            .payload['custom:saml.groups'].replaceAll('[', '')
            .replaceAll(']', '')
            .replace(/, /g, ',')
            .split(',')
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
