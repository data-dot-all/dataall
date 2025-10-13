import { useDispatch } from 'react-redux';

import PropTypes from 'prop-types';
import { Box } from '@mui/material';
import React, { useEffect, useState } from 'react';
import { SET_ERROR } from 'globalErrors';
import { useClient } from 'services';
import { getMetadataForm } from '../services';
import CircularProgress from '@mui/material/CircularProgress';

import { RenderedMetadataForm } from './renderedMetadataForm';

export const MetadataFormPreview = (props) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { metadataForm } = props;
  const [fields, setFields] = useState(metadataForm.fields);
  const [loading, setLoading] = useState(false);

  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(getMetadataForm(metadataForm.uri));
    if (
      !response.errors &&
      response.data &&
      response.data.getMetadataForm !== null
    ) {
      setFields(response.data.getMetadataForm.fields);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Metadata Forms not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };
  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  if (loading) {
    return (
      <Box
        sx={{
          pt: 10,
          minHeight: '400px',
          alignContent: 'center',
          display: 'flex',
          justifyContent: 'center'
        }}
      >
        <CircularProgress size={100} />
      </Box>
    );
  }

  return (
    <RenderedMetadataForm
      fields={fields}
      metadataForm={metadataForm}
      preview={true}
    />
  );
};

MetadataFormPreview.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
