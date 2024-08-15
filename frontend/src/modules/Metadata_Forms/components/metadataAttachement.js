import React, { useEffect, useState } from 'react';

import { useDispatch } from 'react-redux';

import { Box, Card, CardContent, Grid } from '@mui/material';
import { listMetadataForms } from '../services';
import { Defaults } from '../../../design';
import CircularProgress from '@mui/material/CircularProgress';

export const MetadataAttachement = (props) => {
  const client = useClient();
  const dispatch = useDispatch();
  const [selectedForm, setSelectedForm] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formsList, setFormsList] = useState([]);
  const [filter] = useState(Defaults.filter);

  const fetchList = async () => {
    setLoading(true);
    const response = await client.query(listMetadataForms(filter));
    if (!response.errors) {
      setFormsList(response.data.listMetadataForms);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  useEffect(() => {
    if (client) {
      fetchList().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, filter]);

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
    <Grid container spacing={2}>
      <Grid item lg={3} xl={3} xs={6}>
        <Card>
          {formsList.map((form) => (
            <CardContent
              sx={{
                backgroundColor: selectedForm === form ? '#e6e6e6' : 'white'
              }}
              onClick={() => setSelectedForm(form)}
            >
              {form.name}
            </CardContent>
          ))}
        </Card>
      </Grid>
    </Grid>
  );
};
