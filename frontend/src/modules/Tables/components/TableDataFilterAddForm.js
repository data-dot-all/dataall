import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider,
  Button,
  Card,
  TextField,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel
} from '@mui/material';
import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem
} from '@mui/x-data-grid';

import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';

import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useState, useEffect } from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, listDatasetTableColumns } from 'services';
import { createTableDataFilter } from '../services';
import { Defaults } from 'design';

const rowFilterExpressions = [
  {
    value: '=',
    label: '= (equals)',
    acceptsArgument: true
  },
  {
    value: '>',
    label: '> (greater than)',
    acceptsArgument: true
  },
  {
    value: '<',
    label: '< (less than)',
    acceptsArgument: true
  },
  {
    value: '>=',
    label: '>= (greater than or equal)',
    acceptsArgument: true
  },
  {
    value: '<=',
    label: '<= (less than or equal)',
    acceptsArgument: true
  },
  {
    value: '<>',
    label: '<> (not equal)',
    acceptsArgument: true
  },
  {
    value: '!=',
    label: '!= (not equal)',
    acceptsArgument: true
  },
  {
    value: 'BETWEEN',
    label: 'BETWEEN',
    acceptsArgument: true
  },
  {
    value: 'IN',
    label: 'IN',
    acceptsArgument: true
  },
  {
    value: 'LIKE',
    label: 'LIKE',
    acceptsArgument: true
  },
  {
    value: 'NOT',
    label: 'NOT',
    acceptsArgument: true
  },
  {
    value: 'IS NULL',
    label: 'IS NULL',
    acceptsArgument: false
  },
  {
    value: 'IS NOT NULL',
    label: 'IS NOT NULL',
    acceptsArgument: false
  }
];

function EditToolbar(props) {
  const { setRowExpressionRows, setRowModesModel } = props;

  const handleClick = () => {
    const id = Date.now();
    setRowExpressionRows((oldRows) => [
      ...oldRows,
      { id, columnName: '', operator: '', userValue: '', isNew: true }
    ]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [id]: { mode: GridRowModes.Edit, fieldToFocus: 'columnName' }
    }));
  };

  return (
    <GridToolbarContainer>
      <Button color="primary" startIcon={<AddIcon />} onClick={handleClick}>
        Add Row Expression
      </Button>
    </GridToolbarContainer>
  );
}

export const TableDataFilterAddForm = (props) => {
  const { table, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [columns, setColumns] = useState([]);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [pageSize, setPageSize] = useState(5);

  const [rowExpressionRows, setRowExpressionRows] = useState([]);
  const [rowModesModel, setRowModesModel] = useState({});
  const [rowExpressionColumns, setRowExpressionColumns] = useState([]);

  const handleRowEditStop = (params, event) => {
    event.defaultMuiPrevented = true;
  };

  const handleEditClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
  };

  const handleSaveClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
  };

  const handleDeleteClick = (id) => () => {
    setRowExpressionRows(rowExpressionRows.filter((row) => row.id !== id));
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true }
    });

    const editedRow = rowExpressionRows.find((row) => row.id === id);
    if (editedRow.isNew) {
      setRowExpressionRows(rowExpressionRows.filter((row) => row.id !== id));
    }
  };

  const processRowUpdate = (newRow) => {
    const updatedRow = { ...newRow, isNew: false };
    setRowExpressionRows(
      rowExpressionRows.map((row) => (row.id === newRow.id ? updatedRow : row))
    );
    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  const fetchColumns = async () => {
    setLoadingColumns(true);
    const response = await client.query(
      listDatasetTableColumns({
        tableUri: table.tableUri,
        filter: Defaults.selectListFilter
      })
    );
    if (!response.errors) {
      setColumns(
        response.data.listDatasetTableColumns.nodes.map((c) => ({
          id: c.columnUri,
          columnType: c.columnType,
          name:
            c.columnType && c.columnType !== 'column'
              ? `${c.name} (${c.columnType})`
              : c.name,
          type: c.typeName,
          description: c.description
        }))
      );
      setRowExpressionColumns(
        response.data.listDatasetTableColumns.nodes
          .filter((c) => c.columnType === 'column')
          .map((c) => c.name)
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoadingColumns(false);
  };

  useEffect(() => {
    if (client) {
      fetchColumns().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchColumns, table.tableUri]);

  const dataFilterOptions = ['ROW', 'COLUMN'];

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createTableDataFilter({
          filterName: values.filterName,
          SamlGroupName: values.SamlAdminGroupName,
          tableUri: table.tableUri,
          filterType: values.filterType,
          includedCols: values.includedCols,
          rowExpression: values.rowExpression,
          description: values.description
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Data filter created for table', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reload) {
          reload();
        }
        if (onClose) {
          onClose();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  if (!table) {
    return null;
  }

  const header = [
    { field: 'name', headerName: 'Name', width: 300, editable: false },
    { field: 'type', headerName: 'Type', width: 200, editable: false },
    {
      field: 'description',
      headerName: 'Description',
      width: 600
    }
  ];

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Add a new data filter for table {table.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Data filters allow you to restrict access to a table in data.all. They
          are owned by the dataset owners and can be applied on data shares in
          the data.all UI. Each data filter is specific to a particular table.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              filterName: '',
              description: '',
              filterType: 'ROW',
              includedCols: [],
              rowExpression: ''
            }}
            validationSchema={Yup.object().shape({
              filterName: Yup.string()
                .max(255)
                .required('*Connection Name is required'),
              filterType: Yup.string()
                .max(255)
                .required('*Filter Type is required'),
              includedCols: Yup.string().max(255),
              rowExpression: Yup.string().max(255),
              description: Yup.string().max(255)
            })}
            onSubmit={async (
              values,
              { setErrors, setStatus, setSubmitting }
            ) => {
              await submit(values, setStatus, setSubmitting, setErrors);
            }}
          >
            {({
              errors,
              handleChange,
              handleSubmit,
              isSubmitting,
              setFieldValue,
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <Box>
                  <CardContent>
                    <TextField
                      error={Boolean(touched.filterName && errors.filterName)}
                      fullWidth
                      helperText={touched.filterName && errors.filterName}
                      label="Filter Name"
                      placeholder="Name to identify your Data Filter in data.all"
                      name="filterName"
                      onChange={handleChange}
                      value={values.filterName}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      FormHelperTextProps={{
                        sx: {
                          textAlign: 'right',
                          mr: 0
                        }
                      }}
                      error={Boolean(touched.description && errors.description)}
                      fullWidth
                      helperText={`${
                        200 - values.description.length
                      } characters left`}
                      multiline
                      rows={3}
                      label="Data Filter Description"
                      placeholder="Description of Data Filter"
                      name="description"
                      onChange={handleChange}
                      value={values.description}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <FormControl>
                      <FormLabel>Filter Type</FormLabel>
                      <RadioGroup
                        {...props}
                        row
                        name="filterType"
                        value={values.filterType}
                        onChange={(event, value) => {
                          setFieldValue(
                            'filterType',
                            event.currentTarget.value
                          );
                          if (value && value === 'ROW') {
                            setFieldValue('includedCols', []);
                          } else {
                            setFieldValue('rowExpression', '');
                          }
                        }}
                      >
                        {dataFilterOptions.map((option) => (
                          <FormControlLabel
                            value={option}
                            control={<Radio />}
                            label={option}
                          />
                        ))}
                      </RadioGroup>
                    </FormControl>
                  </CardContent>
                </Box>
                <Card>
                  {values.filterType === 'ROW' && (
                    <>
                      {loadingColumns || !rowExpressionColumns ? (
                        <CircularProgress />
                      ) : (
                        <>
                          <CardHeader title="Create a Row Filter Expression" />
                          <Divider />
                          <CardContent>
                            <DataGrid
                              fullWidth
                              autoHeight
                              rows={rowExpressionRows}
                              columns={[
                                {
                                  field: 'columnName',
                                  headerName: 'Column Name',
                                  flex: 1,
                                  editable: true,
                                  type: 'singleSelect',
                                  valueOptions: rowExpressionColumns
                                },
                                {
                                  field: 'operator',
                                  headerName: 'Operator',
                                  flex: 1,
                                  editable: true,
                                  type: 'singleSelect',
                                  valueOptions: rowFilterExpressions
                                },
                                {
                                  field: 'userValue',
                                  headerName: 'Value',
                                  flex: 1,
                                  editable: true
                                },
                                {
                                  field: 'actions',
                                  type: 'actions',
                                  headerName: 'Actions',
                                  flex: 0.5,
                                  cellClassName: 'actions',
                                  getActions: ({ id }) => {
                                    const isInEditMode =
                                      rowModesModel[id]?.mode ===
                                      GridRowModes.Edit;
                                    if (isInEditMode) {
                                      return [
                                        <GridActionsCellItem
                                          icon={<SaveIcon />}
                                          label="Save"
                                          sx={{
                                            color: 'primary.main'
                                          }}
                                          onClick={handleSaveClick(id)}
                                        />,
                                        <GridActionsCellItem
                                          icon={<CancelIcon />}
                                          label="Cancel"
                                          className="textPrimary"
                                          onClick={handleCancelClick(id)}
                                          color="inherit"
                                        />
                                      ];
                                    }
                                    return [
                                      <GridActionsCellItem
                                        icon={<EditIcon />}
                                        label="Edit"
                                        className="textPrimary"
                                        onClick={handleEditClick(id)}
                                        color="inherit"
                                      />,
                                      <GridActionsCellItem
                                        icon={<DeleteIcon />}
                                        label="Delete"
                                        onClick={handleDeleteClick(id)}
                                        color="inherit"
                                      />
                                    ];
                                  }
                                }
                              ]}
                              rowsPerPageOptions={[10]}
                              pageSize={10}
                              editMode="row"
                              rowModesModel={rowModesModel}
                              onRowModesModelChange={handleRowModesModelChange}
                              onRowEditStop={handleRowEditStop}
                              experimentalFeatures={{ newEditingApi: true }}
                              // onRowEditStart={handleRowEditStart}
                              processRowUpdate={processRowUpdate}
                              onProcessRowUpdateError={(error) =>
                                dispatch({
                                  type: SET_ERROR,
                                  error: error.message
                                })
                              }
                              components={{
                                Toolbar: EditToolbar
                              }}
                              componentsProps={{
                                toolbar: {
                                  setRowExpressionRows,
                                  setRowModesModel
                                }
                              }}
                            />
                          </CardContent>
                        </>
                      )}
                    </>
                  )}
                  {values.filterType === 'COLUMN' && (
                    <>
                      {loadingColumns ? (
                        <CircularProgress />
                      ) : (
                        <>
                          <CardHeader title="Select Which Columns To Include on Filter:" />
                          <Divider />
                          <CardContent>
                            {columns.length > 0 ? (
                              <DataGrid
                                fullWidth
                                autoHeight
                                rowSpacingType="border"
                                rows={columns}
                                columns={header}
                                pageSize={pageSize}
                                rowsPerPageOptions={[5, 10, 20]}
                                onPageSizeChange={(newPageSize) =>
                                  setPageSize(newPageSize)
                                }
                                checkboxSelection
                                onSelectionModelChange={(newSelection) => {
                                  setFieldValue('includedCols', newSelection);
                                }}
                                selectionModel={values.includedCols}
                                loading={loadingColumns}
                              />
                            ) : (
                              <Typography
                                align="center"
                                color="textSecondary"
                                variant="subtitle2"
                              >
                                No columns found for this table
                              </Typography>
                            )}
                          </CardContent>
                        </>
                      )}
                      <Typography
                        align="center"
                        color="textSecondary"
                        variant="subtitle2"
                      >
                        Current Selected Columns:{' '}
                        {values.includedCols.join(', ')}
                      </Typography>
                    </>
                  )}
                </Card>
                <Box>
                  <CardContent>
                    <LoadingButton
                      fullWidth
                      startIcon={<GroupAddOutlined fontSize="small" />}
                      color="primary"
                      disabled={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Add Data Filter
                    </LoadingButton>
                  </CardContent>
                </Box>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

TableDataFilterAddForm.propTypes = {
  table: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reload: PropTypes.func
};
