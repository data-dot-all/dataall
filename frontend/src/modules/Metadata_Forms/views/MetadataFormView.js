import React, { useEffect, useCallback, useState } from 'react';

import { Helmet } from 'react-helmet-async';
import { useParams } from 'react-router-dom';
import { SET_ERROR, useDispatch } from '../../../globalErrors';
import { useClient } from '../../../services';
import { getMetadataForm } from '../services';
import { CircularProgress } from '@mui/material';

const MetadataFormView = () => {
  const params = useParams();
  const dispatch = useDispatch();
  const client = useClient();
  const [metadatForm, setMetadataForms] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetadataForm = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getMetadataForm(params.uri));
    if (!response.errors && response.data.getMetadataForm !== null) {
      setMetadataForms(response.data.getMetadataForm);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Metadata Forms not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchMetadataForm().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!metadatForm) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Metadata Form: Metadata Form Details | data.all</title>
      </Helmet>
      {metadatForm.name}
    </>
  );
};

export default MetadataFormView;
