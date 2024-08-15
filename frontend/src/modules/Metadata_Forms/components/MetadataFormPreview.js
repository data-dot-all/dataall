import { useDispatch } from 'react-redux';

import PropTypes from 'prop-types';
import { Box, Card, CardContent, Grid, Typography } from '@mui/material';
import React, { useEffect, useState } from 'react';
import { SET_ERROR } from '../../../globalErrors';
import { useClient } from '../../../services';
import { getMetadataForm } from '../services';
import CircularProgress from '@mui/material/CircularProgress';
import {
  FreeInputField,
  BooleanField,
  DropDownField,
  GlossaryTermField
} from './fields';

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
  const getFieldElement = (field) => {
    if (field.type === 'Boolean') {
      return <BooleanField field={field} />;
    }

    if (field.type === 'Glossary Term') {
      return (
        <GlossaryTermField field={field} client={client} dispatch={dispatch} />
      );
    }

    if (
      ['Integer', 'String'].includes(field.type) &&
      (!field.possibleValues || field.possibleValues.length === 0)
    ) {
      return <FreeInputField field={field} />;
    }

    if (
      ['Integer', 'String'].includes(field.type) &&
      field.possibleValues &&
      field.possibleValues.length > 0
    ) {
      return <DropDownField field={field} />;
    }
  };

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
    <Card>
      {fields.map((field) => (
        <CardContent>
          <Grid container spacing={2}>
            <Grid item lg={3} xl={3} xs={6}>
              {getFieldElement(field)}
            </Grid>
            <Grid
              item
              lg={9}
              xl={9}
              xs={18}
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              <Typography variant="subtitle2" color="textPrimary">
                {field.required && (
                  <span style={{ color: 'red' }}>{'Required. '}</span>
                )}
                <span>{field.description}</span>
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      ))}
    </Card>
  );
};

MetadataFormPreview.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
