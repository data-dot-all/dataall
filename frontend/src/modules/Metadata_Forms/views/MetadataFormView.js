import React, { useEffect, useCallback, useState } from 'react';

import { Helmet } from 'react-helmet-async';
import { SET_ERROR, useDispatch } from '../../../globalErrors';
import { fetchEnums, useClient } from '../../../services';
import { getMetadataForm } from '../services';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  Box,
  Breadcrumbs,
  Button,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { ChevronRightIcon, useSettings } from '../../../design';
import { FaTrash } from 'react-icons/fa';
import {
  MetadataFormInfo,
  MetadataFormFields,
  MetadataFormPreview,
  MetadataFormEnforcement
} from '../components';

const MetadataFormView = () => {
  const params = useParams();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const tabs = [
    { label: 'Form Info', value: 'info' },
    { label: 'Fields', value: 'fields' },
    { label: 'Enforcement', value: 'enforcement' },
    { label: 'Preview', value: 'preview' }
  ];
  const [metadataForm, setMetadataForms] = useState(null);
  const [currentTab, setCurrentTab] = useState(null);
  const [loading, setLoading] = useState(true);
  const [visibilityDict, setVisibilityDict] = useState({});
  const [fieldTypeOptions, setFieldTypeOptions] = useState([]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  const handleDeleteObjectModalOpen = () => {};

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

  const fetchMFEnums = async () => {
    try {
      const enums = await fetchEnums(client, [
        'MetadataFormVisibility',
        'MetadataFormFieldType'
      ]);
      if (enums['MetadataFormVisibility'].length > 0) {
        let tmpVisibilityDict = {};
        enums['MetadataFormVisibility'].map((x) => {
          tmpVisibilityDict[x.name] = x.value;
        });
        setVisibilityDict(tmpVisibilityDict);
      } else {
        const error = 'Could not fetch visibility options';
        dispatch({ type: SET_ERROR, error });
      }
      if (enums['MetadataFormFieldType'].length > 0) {
        setFieldTypeOptions(enums['MetadataFormFieldType']);
      } else {
        const error = 'Could not fetch field type options';
        dispatch({ type: SET_ERROR, error });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  useEffect(() => {
    if (client) {
      fetchMetadataForm().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchMFEnums().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
    setCurrentTab('info');
  }, [client, dispatch]);

  if (loading) {
    return (
      <>
        <Helmet>
          <title>Metadata Form: Metadata Form Details | data.all</title>
        </Helmet>
        <Box
          sx={{
            backgroundColor: 'background.default',
            minHeight: '100%',
            overflow: 'hidden',
            pl: '45%',
            pt: '10%'
          }}
        >
          <Container maxWidth={settings.compact ? 'xl' : false}>
            <CircularProgress size={100} />
          </Container>
        </Box>
      </>
    );
  }
  if (!metadataForm) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Metadata Form: Metadata Form Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                {metadataForm.name}
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Discover
                </Typography>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/metadata-forms"
                  variant="subtitle2"
                >
                  Metadata Forms
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/metadata-forms/${metadataForm.uri}`}
                  variant="subtitle2"
                >
                  {metadataForm.name}
                </Link>
              </Breadcrumbs>
            </Grid>

            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  startIcon={<FaTrash size={15} />}
                  sx={{ mt: 1 }}
                  onClick={handleDeleteObjectModalOpen}
                  type="button"
                  variant="outlined"
                >
                  Delete
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Tabs
              indicatorColor="primary"
              onChange={handleTabsChange}
              scrollButtons="auto"
              textColor="primary"
              value={currentTab}
              variant="fullWidth"
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'info' && (
              <MetadataFormInfo
                metadataForm={metadataForm}
                visibilityDict={visibilityDict}
              />
            )}
            {currentTab === 'fields' && (
              <MetadataFormFields
                metadataForm={metadataForm}
                visibilityDict={visibilityDict}
                fieldTypeOptions={fieldTypeOptions}
              />
            )}
            {currentTab === 'enforcement' && (
              <MetadataFormEnforcement metadataForm={metadataForm} />
            )}
            {currentTab === 'preview' && (
              <MetadataFormPreview metadataForm={metadataForm} />
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default MetadataFormView;