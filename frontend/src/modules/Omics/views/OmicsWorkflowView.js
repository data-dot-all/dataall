import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Typography
} from '@mui/material';
import { useClient } from 'services';
import { useSettings, PlusIcon } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';

import { getOmicsWorkflow } from '../services';
import { OmicsWorkflowDetails } from '../components';

const OmicsWorkflowView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const [loading, setLoading] = useState(true);
  const [omicsWorkflow, setOmicsWorkflow] = useState(null);

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getOmicsWorkflow(params.uri));
    if (!response.errors) {
      setOmicsWorkflow(response.data.getOmicsWorkflow);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Omics Workflow not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!omicsWorkflow) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Omics: Workflow Details</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container spacing={0.5} alignItems="center">
            <Grid item justifyContent="center" md={10} lg={10} xl={10}>
              <Typography color="textPrimary" variant="h5">
                Omics Workflow
              </Typography>
              <Typography color="textSecondary" variant="h5">
                {omicsWorkflow.name}
              </Typography>
            </Grid>
            <Grid item justifyContent="center" md={2} lg={2} xl={2}>
              <Box sx={{ m: 1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<PlusIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  to={`/console/omics/workflows/${omicsWorkflow.workflowUri}/runs/new/`}
                  variant="contained"
                >
                  Create Run
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Divider />
          <Box sx={{ mt: 3 }}>
            <OmicsWorkflowDetails workflow={omicsWorkflow} />
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default OmicsWorkflowView;
