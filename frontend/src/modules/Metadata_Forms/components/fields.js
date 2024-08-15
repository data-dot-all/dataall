import {
  Autocomplete,
  Checkbox,
  FormControlLabel,
  TextField
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { getGlossaryTree } from '../../Glossaries/services';
import { SET_ERROR } from '../../../globalErrors';

export const FreeInputField = (props) => {
  const { field } = props;
  return (
    <TextField
      sx={{ width: '100%' }}
      label={field.name}
      name={field.name}
      required={field.required}
    ></TextField>
  );
};
FreeInputField.propTypes = {
  field: PropTypes.any.isRequired
};

export const BooleanField = (props) => {
  const { field } = props;
  return (
    <FormControlLabel
      sx={{ pl: 1 }}
      control={<Checkbox id={field.name} />}
      label={field.name}
    />
  );
};

BooleanField.propTypes = {
  field: PropTypes.any.isRequired
};

export const GlossaryTermField = (props) => {
  const { field, client, dispatch } = props;

  const [glossaryOptions, setGlossaryOptions] = useState([]);

  const fetchGlossaryTerms = async () => {
    const response = await client.query(
      getGlossaryTree({
        nodeUri: field.glossaryNodeUri,
        filter: { pageSize: 500 }
      })
    );
    if (!response.errors && response.data.getGlossary !== null) {
      setGlossaryOptions(
        response.data.getGlossary.tree.nodes.filter(
          (node) => node.__typename === 'Term'
        )
      );
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
      renderInput={(params) => (
        <TextField
          sx={{ width: '100%' }}
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
  const { field } = props;
  return (
    <Autocomplete
      disablePortal
      options={field.possibleValues}
      renderInput={(params) => (
        <TextField
          sx={{ width: '100%' }}
          {...params}
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
