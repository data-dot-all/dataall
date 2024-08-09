import { useDispatch } from 'react-redux';

import React, { useEffect, useState } from 'react';

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
  Autocomplete,
  Tooltip
} from '@mui/material';
import {
  Scrollbar,
  SearchIcon,
  AsteriskIcon,
  PencilAltIcon,
  SaveIcon,
  PlusIcon
} from '../../../design';
import { SET_ERROR } from '../../../globalErrors';
import Checkbox from '@mui/material/Checkbox';
import {
  //  createMetadataFormFields,
  getMetadataForm
  //  deleteMetadataFormField
} from '../services';
import { useClient } from '../../../services';
import { GridActionsCellItem } from '@mui/x-data-grid';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SettingsBackupRestoreOutlinedIcon from '@mui/icons-material/SettingsBackupRestoreOutlined';
import { batchMetadataFormFieldUpdates } from '../services/batchMetadataFormFieldUpdates';
import CircularProgress from '@mui/material/CircularProgress';

const EditTable = (props) => {
  const { fields, fieldTypeOptions, saveChanges, formUri } = props;
  const [localFields, setLocalFields] = useState(fields);

  const updateField = (index, propertyName, value) => {
    localFields[index][propertyName] = value;
    setLocalFields([...localFields]);
  };
  const addField = () => {
    localFields.push({
      name: 'New Field',
      required: false,
      metadataFormUri: formUri,
      type: fieldTypeOptions[0].value,
      possibleValues: [],
      deleted: false
    });
    setLocalFields([...localFields]);
  };

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell sx={{ width: '20px' }}>Required</TableCell>
          <TableCell>Name</TableCell>
          <TableCell>Type</TableCell>
          <TableCell sx={{ width: '30%' }}>Description</TableCell>
          <TableCell sx={{ width: '15%' }}>
            Values (any, if not specified)
          </TableCell>
          <TableCell sx={{ width: '20px' }}>
            <Button
              color="primary"
              startIcon={<SaveIcon size={15} />}
              sx={{ mt: 1 }}
              onClick={() => {
                saveChanges(localFields);
              }}
              type="button"
              variant="outlined"
            >
              Save
            </Button>
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        <TableRow>
          <TableCell colSpan={6}>
            <Button
              color="primary"
              startIcon={<PlusIcon size={15} />}
              sx={{ mt: 1 }}
              onClick={addField}
              type="button"
            >
              Add field
            </Button>
          </TableCell>
        </TableRow>
        {localFields.length === 0 ? (
          <TableRow>
            <TableCell colSpan={6} align="center">
              No fields found
            </TableCell>
          </TableRow>
        ) : (
          localFields.map((field, index) => (
            <TableRow
              sx={{
                backgroundColor: field.deleted ? 'whitesmoke' : 'white'
              }}
            >
              <TableCell>
                <Checkbox
                  defaultChecked={field.required}
                  disabled={field.deleted}
                  onChange={(event) => {
                    updateField(index, 'required', event.target.value === 'on');
                  }}
                />
              </TableCell>
              <TableCell>
                <TextField
                  disabled={field.deleted}
                  defaultValue={field.name}
                  onKeyUp={(event) => {
                    updateField(index, 'name', event.target.value);
                  }}
                  sx={{ width: '100%' }}
                />
              </TableCell>
              <TableCell>
                <Autocomplete
                  disablePortal
                  disabled={field.deleted}
                  options={fieldTypeOptions.map((option) => option.value)}
                  defaultValue={field.type}
                  onChange={(event, value) => {
                    updateField(
                      index,
                      'type',
                      value || fieldTypeOptions[0].value
                    );
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
                <TextField
                  disabled={field.deleted}
                  defaultValue={field.description}
                  sx={{ width: '100%' }}
                  onKeyUp={(event) => {
                    updateField(index, 'description', event.target.value);
                  }}
                />
              </TableCell>
              <TableCell>
                <TextField
                  defaultValue={field.possibleValues.join(', ')}
                  disabled={field.deleted}
                  onKeyUp={(event) => {
                    updateField(
                      index,
                      'possibleValues',
                      event.target.value.split(',')
                    );
                  }}
                  sx={{ width: '100%' }}
                />
              </TableCell>
              <TableCell
                sx={{
                  width: '20px',
                  alignContent: 'center',
                  textAlign: 'center'
                }}
              >
                <Tooltip title={field.deleted ? 'Restore' : 'Delete'}>
                  <GridActionsCellItem
                    icon={
                      field.deleted ? (
                        <SettingsBackupRestoreOutlinedIcon />
                      ) : (
                        <DeleteIcon />
                      )
                    }
                    label={field.deleted ? 'Restore' : 'Delete'}
                    sx={{
                      color: 'primary.main'
                    }}
                    onClick={() => {
                      updateField(index, 'deleted', !field.deleted);
                    }}
                  />
                </Tooltip>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
};

EditTable.propTypes = {
  fields: PropTypes.array.isRequired,
  fieldTypeOptions: PropTypes.array.isRequired,
  saveChanges: PropTypes.func.isRequired,
  formUri: PropTypes.string.isRequired
};

const DisplayTable = (props) => {
  const { fields, startEdit } = props;
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell sx={{ width: '20px' }}>Required</TableCell>
          <TableCell>Name</TableCell>
          <TableCell>Type</TableCell>
          <TableCell sx={{ width: '30%' }}>Description</TableCell>
          <TableCell sx={{ width: '15%' }}>
            Values (any, if not specified)
          </TableCell>
          <TableCell sx={{ width: '20px', alignContent: 'center' }}>
            <Button
              color="primary"
              startIcon={<PencilAltIcon size={15} />}
              sx={{ mt: 1 }}
              onClick={startEdit}
              type="button"
              variant="outlined"
            >
              Edit
            </Button>
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
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
              <TableCell>{field.description}</TableCell>
              <TableCell>{field.possibleValues}</TableCell>
              <TableCell></TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
};
DisplayTable.propTypes = {
  fields: PropTypes.array.isRequired,
  startEdit: PropTypes.func.isRequired
};

export const MetadataFormFields = (props) => {
  const dispatch = useDispatch();
  const client = useClient();
  const { metadataForm, fieldTypeOptions } = props;
  const [loading, setLoading] = useState(false);
  const [editOn, setEditOn] = useState(false);
  const [fields, setFields] = useState(metadataForm.fields);
  const [inputValue, setInputValue] = useState('');
  const [filter, setFilter] = useState({});

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const startEdit = () => {
    setEditOn(true);
  };

  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(getMetadataForm(metadataForm.uri));
    if (!response.errors && response.data.getMetadataForm !== null) {
      setFields(response.data.getMetadataForm.fields);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Metadata Forms not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };

  const saveChanges = async (updatedFields) => {
    setLoading(true);
    // remove new fields (not yet saved in DB), that were deleted during editing
    const data = updatedFields.filter((field) => !field.deleted || field.uri);
    data.forEach((field) => {
      delete field.__typename;
    });
    const response = await client.mutate(
      batchMetadataFormFieldUpdates(metadataForm.uri, data)
    );
    if (
      !response.errors &&
      response.data &&
      response.data.batchMetadataFormFieldUpdates !== null
    ) {
      setFields(response.data.batchMetadataFormFieldUpdates);
      setEditOn(false);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Update failed';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  useEffect(() => {
    fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
  }, [client, dispatch]);

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
            disabled="true"
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
            placeholder="Search (temporary deisabled)"
            value={inputValue}
            variant="outlined"
          />
        </Box>
        <Divider />
        {loading ? (
          <Box
            sx={{
              p: 2,
              minHeight: '400px',
              alignContent: 'center',
              display: 'flex',
              justifyContent: 'center'
            }}
          >
            <CircularProgress size={100} />
          </Box>
        ) : (
          <Scrollbar>
            <Box
              sx={{
                p: 2,
                minHeight: '400px'
              }}
            >
              {editOn ? (
                <EditTable
                  fields={fields}
                  fieldTypeOptions={fieldTypeOptions}
                  saveChanges={saveChanges}
                  formUri={metadataForm.uri}
                />
              ) : (
                <DisplayTable fields={fields} startEdit={startEdit} />
              )}
            </Box>
          </Scrollbar>
        )}
      </Card>
    </Box>
  );
};

MetadataFormFields.propTypes = {
  metadataForm: PropTypes.any.isRequired,
  fieldTypeOptions: PropTypes.any.isRequired
};
