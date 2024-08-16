import React, { useEffect, useState } from 'react';

import { useDispatch } from 'react-redux';

import {
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import {
  getAttachedMetadataForm,
  getMetadataForm,
  listAttachedMetadataForms,
  listMetadataForms
} from '../services';
import { Defaults, PlusIcon } from '../../../design';
import CircularProgress from '@mui/material/CircularProgress';
import { useClient } from '../../../services';
import { RenderedMetadataForm } from './renderedMetadataForm';
import { SET_ERROR } from '../../../globalErrors';
import { AttachedFormCard } from './AttachedFormCard';
import DoNotDisturbAltOutlinedIcon from '@mui/icons-material/DoNotDisturbAltOutlined';

export const MetadataAttachement = (props) => {
  const { entityType, entityUri } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [selectedForm, setSelectedForm] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingFields, setLoadingFields] = useState(false);
  const [formsList, setFormsList] = useState([]);
  const [fields, setFields] = useState([]);
  const [filter] = useState({
    ...Defaults.filter,
    entityType: entityType,
    entityUri: entityUri
  });
  const [addNewForm, setAddNewForm] = useState(false);
  const [availableForms, setAvailableForms] = useState([]);

  const fetchAvailableForms = async () => {
    const response = await client.query(listMetadataForms({}));
    if (!response.errors) {
      setAvailableForms(
        response.data.listMetadataForms.nodes.map((form) => ({
          label: form.name,
          value: form.uri,
          form: form
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchList = async () => {
    setLoading(true);
    const response = await client.query(listAttachedMetadataForms(filter));
    if (!response.errors) {
      setFormsList(response.data.listAttachedMetadataForms.nodes);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  const fetchFields = async (uri) => {
    setLoadingFields(true);
    const response = await client.query(getMetadataForm(uri));
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
    setLoadingFields(false);
  };
  const fetchAttachedFields = async (uri) => {
    setLoadingFields(true);
    const response = await client.query(getAttachedMetadataForm(uri));
    if (
      !response.errors &&
      response.data &&
      response.data.getAttachedMetadataForm !== null
    ) {
      setFields(response.data.getAttachedMetadataForm.fields);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Metadata Forms not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoadingFields(false);
  };

  useEffect(() => {
    if (client) {
      fetchList().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
      fetchAvailableForms().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
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
    <Grid container spacing={2} sx={{ height: 'calc(100vh - 320px)', mb: -5 }}>
      <Grid item lg={3} xl={3} xs={6}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Button
              color="primary"
              startIcon={<PlusIcon size={15} />}
              sx={{ mt: 1 }}
              type="button"
              onClick={() => {
                setSelectedForm(null);
                setAddNewForm(true);
              }}
            >
              Attach form
            </Button>
          </CardContent>
          <Divider />
          {addNewForm && (
            <CardContent>
              <Autocomplete
                disablePortal
                options={availableForms}
                onChange={async (event, value) => {
                  if (value) {
                    setSelectedForm(value.form);
                    await fetchFields(value.value);
                  } else setSelectedForm(null);
                }}
                renderInput={(params) => (
                  <TextField
                    sx={{ width: '100%' }}
                    {...params}
                    label="Select Metadata Form"
                    variant="outlined"
                  />
                )}
              />
            </CardContent>
          )}
          {formsList.length > 0 ? (
            formsList.map((attachedForm) => (
              <CardContent
                sx={{
                  backgroundColor:
                    selectedForm === attachedForm ? '#e6e6e6' : 'white'
                }}
                onClick={async () => {
                  setSelectedForm(attachedForm);
                  await fetchAttachedFields(attachedForm.uri);
                }}
              >
                {attachedForm.metadataForm.name}
              </CardContent>
            ))
          ) : (
            <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
              <DoNotDisturbAltOutlinedIcon sx={{ mr: 1 }} />
              <Typography variant="subtitle2" color="textPrimary">
                No Metadata Forms Attached
              </Typography>
            </CardContent>
          )}
        </Card>
      </Grid>
      <Grid item lg={9} xl={9} xs={6}>
        {loadingFields && (
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
        )}
        {addNewForm && selectedForm && !loadingFields && (
          <RenderedMetadataForm
            fields={fields}
            metadataForm={selectedForm}
            preview={false}
            onCancel={() => {
              setAddNewForm(false);
              setSelectedForm(null);
              setFields([]);
            }}
            entityUri={entityUri}
            entityType={entityType}
            onSubmit={(attachedForm) => {
              setSelectedForm(attachedForm);
              setFields(attachedForm.fields);
              setAddNewForm(false);
            }}
          />
        )}
        {!addNewForm && !loadingFields && selectedForm && (
          <AttachedFormCard fields={fields} attachedForm={selectedForm} />
        )}
      </Grid>
    </Grid>
  );
};
