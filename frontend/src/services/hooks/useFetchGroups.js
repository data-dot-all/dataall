import { listEnvironmentGroups, useClient } from 'services';
import { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { Defaults } from 'design';

// TODO DRY fetchGroup usages using this func
export const useFetchGroups = (environment) => {
  const client = useClient();
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const dispatch = useDispatch();
  const fetchGroups = async (environmentUri) => {
    try {
      setLoadingGroups(true);
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.selectListFilter,
          environmentUri
        })
      );
      if (!response.errors) {
        setGroupOptions(
          response.data.listEnvironmentGroups.nodes.map((g) => ({
            value: g.groupUri,
            label: g.groupUri
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingGroups(false);
    }
  };

  useEffect(() => {
    if (client && environment) {
      fetchGroups(environment.environmentUri).catch((e) =>
        dispatch({
          type: SET_ERROR,
          error: e.message
        })
      );
    }
  }, [client, environment, dispatch]);

  return { groupOptions, loadingGroups };
};
