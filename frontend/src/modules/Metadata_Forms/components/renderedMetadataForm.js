import { Card, CardContent, Grid, Typography } from '@mui/material';
import React from 'react';
import {
  BooleanField,
  DropDownField,
  FreeInputField,
  GlossaryTermField
} from './fields';
import { useClient } from '../../../services';
import { useDispatch } from 'react-redux';

export const RenderedMetadataForm = (props) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { fields } = props;

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
