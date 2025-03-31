import {
  Autocomplete,
  Checkbox,
  FormControlLabel,
  TextField
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { getGlossaryTree } from '../../Glossaries/services';
import { SET_ERROR } from 'globalErrors';
import { Defaults } from 'design';

export const FreeInputField = (props) => {
  const { field, onChange, errors } = props;
  return (
    <TextField
      sx={{ width: '100%' }}
      label={field.name}
      error={errors[field.name]}
      name={field.name}
      defaultValue={field.value}
      onKeyUp={(event) => {
        onChange(event.target.value);
      }}
    ></TextField>
  );
};
FreeInputField.propTypes = {
  field: PropTypes.any.isRequired
};

export const BooleanField = (props) => {
  const { field, onChange } = props;
  return (
    <FormControlLabel
      sx={{ pl: 1 }}
      control={
        <Checkbox
          id={field.name}
          defaultChecked={
            field.value !== undefined ? JSON.parse(field.value) : false
          }
          onChange={(event, checked) => onChange(checked)}
        />
      }
      label={field.name}
    />
  );
};

BooleanField.propTypes = {
  field: PropTypes.any.isRequired
};

export const GlossaryTermField = (props) => {
  const { field, client, dispatch, onChange, errors } = props;

  const [glossaryOptions, setGlossaryOptions] = useState([]);

  const fetchGlossaryTerms = async () => {
    const response = await client.query(
      getGlossaryTree({
        nodeUri: field.glossaryNodeUri,
        filter: { ...Defaults.selectListFilter, nodeType: 'T' }
      })
    );
    if (!response.errors && response.data.getGlossary !== null) {
      setGlossaryOptions(response.data.getGlossary.tree.nodes);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Glossary not found';
      dispatch({ type: SET_ERROR, error });
    }
  };

  useEffect(() => {
    if (client) {
      fetchGlossaryTerms().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  return (
    <Autocomplete
      options={glossaryOptions}
      onChange={(event, value) => onChange(value.nodeUri)}
      defaultValue={field.value}
      renderInput={(params) => (
        <TextField
          sx={{ width: '100%' }}
          error={Boolean(errors) && Boolean(errors[field.name])}
          {...params}
          label={field.name}
          variant="outlined"
        />
      )}
    />
  );
};

GlossaryTermField.propTypes = {
  field: PropTypes.any.isRequired,
  client: PropTypes.any.isRequired,
  dispatch: PropTypes.any.isRequired
};

export const DropDownField = (props) => {
  const { field, onChange, errors } = props;
  return (
    <Autocomplete
      disablePortal
      options={field.possibleValues}
      defaultValue={field.value}
      onChange={(event, value) => onChange(value)}
      renderInput={(params) => (
        <TextField
          sx={{ width: '100%' }}
          {...params}
          error={Boolean(errors) && Boolean(errors[field.name])}
          label={field.name}
          variant="outlined"
        />
      )}
    />
  );
};

DropDownField.propTypes = {
  field: PropTypes.any.isRequired
};
