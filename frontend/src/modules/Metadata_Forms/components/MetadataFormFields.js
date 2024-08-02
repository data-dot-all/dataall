import { useDispatch } from 'react-redux';
import SaveIcon from '@mui/icons-material/Save';

import React, { useState } from 'react';

import PropTypes from 'prop-types';
import {
  Table,
  TableCell,
  TableHead,
  TableRow,
  TableBody,
  Card,
  Box,
  TextField,
  InputAdornment,
  Divider,
  Button,
  Autocomplete
} from '@mui/material';
import { Scrollbar, SearchIcon, AsteriskIcon } from '../../../design';
import { SET_ERROR } from '../../../globalErrors';
import Checkbox from '@mui/material/Checkbox';
import {
  createMetadataFormFields,
  getMetadataForm,
  deleteMetadataFormField
} from '../services';
import { useClient } from '../../../services';
import { GridActionsCellItem } from '@mui/x-data-grid';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';

const NewFieldRow = (props) => {
  const { onRemove, onChange, fieldTypeOptions, saveField } = props;
  const [name, setName] = useState('');
  const [type, setType] = useState('String');
  const [required, setRequired] = useState(false);
  const [possibleValues, setPossibleValues] = useState('');

  const saveChanged = () => {
    const data = {
      name: name.length > 0 ? name : null,
      type: type,
      required: required,
      possibleValues: possibleValues.split(',')
    };
    onChange(data);
  };

  const save = () => {
    const data = {
      name: name.length > 0 ? name : null,
      type: type,
      required: required,
      possibleValues: possibleValues.split(',')
    };
    saveField(data);
  };

  return (
    <TableRow>
      <TableCell>
        <Checkbox
          onChange={(event) => {
            setRequired(event.target.value === 'on');
            saveChanged();
          }}
        />
      </TableCell>
      <TableCell>
        <TextField
          onChange={(event) => {
            setName(event.target.value);
            saveChanged();
          }}
          sx={{ width: '100%' }}
        />
      </TableCell>
      <TableCell>
        <Autocomplete
          disablePortal
          options={fieldTypeOptions.map((option) => option.value)}
          defaultValue={fieldTypeOptions[0].value}
          onChange={(event, value) => {
            if (value) {
              setType(value);
            } else {
              setType(fieldTypeOptions[0].value);
            }
            saveChanged();
          }}
          renderInput={(params) => (
            <TextField
              sx={{ minWidth: '150px' }}
              {...params}
              label="Type"
              variant="outlined"
            />
          )}
        />
      </TableCell>
      <TableCell>
        <TextField sx={{ width: '100%' }} />
      </TableCell>
      <TableCell>
        <TextField
          onChange={(event) => {
            setPossibleValues(event.target.value);
            saveChanged();
          }}
          sx={{ width: '100%' }}
        />
      </TableCell>
      <TableCell>
        <GridActionsCellItem
          icon={<SaveIcon />}
          label="Save"
          sx={{
            color: 'primary.main'
          }}
          onClick={save}
        />
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Save"
          sx={{
            color: 'primary.main'
          }}
          onClick={() => {
            onRemove();
          }}
        />
      </TableCell>
    </TableRow>
  );
};

NewFieldRow.propTypes = {
  onRemove: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  fieldTypeOptions: PropTypes.array.isRequired,
  saveField: PropTypes.func.isRequired
};

export const MetadataFormFields = (props) => {
  const dispatch = useDispatch();
  const client = useClient();
  const { metadataForm, fieldTypeOptions } = props;
  const [fields, setFields] = useState(metadataForm.fields);
  const [inputValue, setInputValue] = useState('');
  const [filter, setFilter] = useState({});
  const [newFields, setNewFields] = useState([]);
  const handleAddField = () => {
    setNewFields([...newFields, {}]);
  };

  const handleRemoveNewField = (index) => {
    newFields.splice(index, 1);
    setNewFields([...newFields]);
  };

  const handleFieldChange = (index, value) => {
    const newFieldsArray = [...newFields];
    newFieldsArray[index] = value;
    setNewFields(newFieldsArray);
  };

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const saveAllNewFields = async () => {
    const data = newFields.map((field) => {
      return {
        name: field.name,
        type: field.type,
        required: field.required,
        possibleValues: field.possibleValues
      };
    });
    await saveFields(metadataForm.uri, data);
    setNewFields([]);
  };

  const saveFields = async (uri, data) => {
    const response = await client.mutate(
      createMetadataFormFields(metadataForm.uri, data)
    );
    if (!response.errors) {
      await fetchItems();
    }
  };

  const deleteField = async (uri) => {
    await client.mutate(deleteMetadataFormField(metadataForm.uri, uri));
    await fetchItems();
  };

  const fetchItems = async () => {
    const response = await client.query(getMetadataForm(metadataForm.uri));
    if (!response.errors && response.data.getMetadataForm !== null) {
      setFields(response.data.getMetadataForm.fields);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Metadata Forms not found';
      dispatch({ type: SET_ERROR, error });
    }
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  return (
    <Box>
      <Card>
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flexWrap: 'wrap',
            m: -1,
            p: 2
          }}
        >
          <TextField
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              )
            }}
            onChange={handleInputChange}
            onKeyUp={handleInputKeyup}
            placeholder="Search"
            value={inputValue}
            variant="outlined"
          />
        </Box>
        <Divider />
        <Box
          sx={{
            pl: 2,
            pt: 2
          }}
        >
          <Button onClick={handleAddField}>Add field</Button>
          <Button onClick={saveAllNewFields}>Save fields</Button>
        </Box>
        <Scrollbar>
          <Box
            sx={{
              p: 2,
              minHeight: '400px'
            }}
          >
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: '20px' }}>Required</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Values (any, if not specified)</TableCell>
                  <TableCell></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {newFields.map((field, index) => (
                  <NewFieldRow
                    onRemove={() => handleRemoveNewField(index)}
                    onChange={(value) => handleFieldChange(index, value)}
                    fieldTypeOptions={fieldTypeOptions}
                    saveField={async (data) => {
                      setNewFields([...newFields.splice(index, 1)]);
                      await saveFields(metadataForm.uri, [data]);
                    }}
                    index={() => {
                      return index;
                    }}
                  />
                ))}
                {fields.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No fields found
                    </TableCell>
                  </TableRow>
                ) : (
                  fields.map((field) => (
                    <TableRow key={field.uri}>
                      <TableCell
                        sx={{
                          textAlign: 'center'
                        }}
                      >
                        {field.required ? <AsteriskIcon /> : ''}
                      </TableCell>
                      <TableCell>{field.name}</TableCell>
                      <TableCell>{field.type}</TableCell>
                      <TableCell></TableCell>
                      <TableCell>{field.possibleValues}</TableCell>
                      <TableCell>
                        <GridActionsCellItem
                          icon={<DeleteIcon />}
                          label="Save"
                          sx={{
                            color: 'primary.main'
                          }}
                          onClick={async () => {
                            await deleteField(field.uri);
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Box>
        </Scrollbar>
      </Card>
    </Box>
  );
};

MetadataFormFields.propTypes = {
  metadataForm: PropTypes.any.isRequired,
  visibilityDict: PropTypes.any.isRequired,
  fieldTypeOptions: PropTypes.any.isRequired
};
