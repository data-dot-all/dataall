import React, { useState } from 'react';

import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography
} from '@mui/material';
import {
  BooleanField,
  DropDownField,
  FreeInputField,
  GlossaryTermField
} from './fields';
import { useClient } from '../../../services';
import { useDispatch } from 'react-redux';
import { Formik } from 'formik';
import { LoadingButton } from '@mui/lab';
import SendIcon from '@mui/icons-material/Send';
import { createAttachedMetadataForm } from '../services';
import { SET_ERROR } from '../../../globalErrors';

export const RenderedMetadataForm = (props) => {
  const client = useClient();
  const dispatch = useDispatch();
  const {
    fields,
    onSubmit,
    onCancel,
    entityUri,
    entityType,
    metadataForm,
    preview
  } = props;

  const [localFields, setLocalFields] = useState([...fields]);
  localFields.forEach((field, index) => {
    if (field.type === 'Boolean' && field.value === undefined) {
      field.value = false;
    }
  });

  const updateFields = (index, value) => {
    const updatedFields = [...localFields];
    updatedFields[index] = {
      ...updatedFields[index],
      value: value
    };
    setLocalFields(updatedFields);
  };

  const getFieldElement = (field, index, errors) => {
    if (field.type === 'Boolean') {
      return (
        <BooleanField
          field={field}
          errors={errors}
          onChange={(value) => updateFields(index, value)}
        />
      );
    }

    if (field.type === 'Glossary Term') {
      return (
        <GlossaryTermField
          field={field}
          client={client}
          errors={errors}
          dispatch={dispatch}
          onChange={(value) => updateFields(index, value)}
        />
      );
    }

    if (
      ['Integer', 'String'].includes(field.type) &&
      (!field.possibleValues || field.possibleValues.length === 0)
    ) {
      return (
        <FreeInputField
          field={field}
          errors={errors}
          onChange={(value) => updateFields(index, value)}
        />
      );
    }

    if (
      ['Integer', 'String'].includes(field.type) &&
      field.possibleValues &&
      field.possibleValues.length > 0
    ) {
      return (
        <DropDownField
          field={field}
          errors={errors}
          onChange={(value) => updateFields(index, value)}
        />
      );
    }
  };

  const submit = async (values, setStatus, setSubmitting, setErrors) => {
    const errors = {};
    localFields.forEach((field) => {
      if (field.required && !field.value) {
        errors[field.name] = true;
      }
    });
    if (Object.keys(errors).length > 0) {
      setErrors(errors);
      setSubmitting(false);
      return;
    }
    const input = {
      entityUri: entityUri,
      entityType: entityType,
      fields: localFields.map((field) => ({
        fieldUri: field.uri,
        value: JSON.stringify(field.value) || 'null'
      }))
    };
    const response = await client.mutate(
      createAttachedMetadataForm(metadataForm.uri, input)
    );
    if (!response.errors && response.data.createAttachedMetadataForm !== null) {
      onSubmit(response.data.createAttachedMetadataForm);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Fail to attach Metadata Form';
      dispatch({ type: SET_ERROR, error });
    }
    setSubmitting(false);
  };

  return (
    <Card sx={{ height: '100%' }}>
      <Formik
        initialValues={{}}
        onSubmit={async (values, { setErrors, setStatus, setSubmitting }) => {
          await submit(values, setStatus, setSubmitting, setErrors);
        }}
      >
        {({
          errors,
          handleBlur,
          handleChange,
          handleSubmit,
          isSubmitting,
          setFieldValue,
          touched,
          values
        }) => (
          <form onSubmit={handleSubmit}>
            <CardContent>
              <Grid container>
                <Grid item lg={8} xl={8}>
                  <CardHeader title={metadataForm.name} />
                </Grid>
                <Grid item lg={4} xl={4}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      p: 2
                    }}
                  >
                    <LoadingButton
                      startIcon={<SendIcon fontSize="small" />}
                      color="primary"
                      disabled={isSubmitting || preview}
                      type="submit"
                      variant="contained"
                    >
                      Attach
                    </LoadingButton>

                    <Button
                      sx={{ ml: 1 }}
                      onClick={onCancel}
                      color="primary"
                      variant="outlined"
                      disabled={isSubmitting || preview}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>

            {localFields.map((field, index) => (
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item lg={3} xl={3} xs={6}>
                    {getFieldElement(field, index, errors)}
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
          </form>
        )}
      </Formik>
    </Card>
  );
};
