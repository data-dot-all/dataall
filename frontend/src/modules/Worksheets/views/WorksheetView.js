import { PlayArrowOutlined, SaveOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CircularProgress,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  MenuItem,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { CgHashtag } from 'react-icons/cg';
import { FaTrash } from 'react-icons/fa';
import { VscSymbolString } from 'react-icons/vsc';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Defaults,
  DeleteObjectWithFrictionModal,
  PencilAltIcon,
  Scrollbar
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import {
  listDatasetTables,
  getSharedDatasetTables,
  listDatasetTableColumns,
  listS3DatasetsOwnedByEnvGroup,
  listValidEnvironments,
  useClient
} from 'services';
import {
  deleteWorksheet,
  getWorksheet,
  listS3DatasetsSharedWithEnvGroup,
  listSharedDatasetTableColumns,
  runAthenaSqlQuery,
  updateWorksheet
} from '../services';
import {
  SQLQueryEditor,
  WorksheetEditFormModal,
  WorksheetResult
} from '../components';

const WorksheetView = () => {
  const navigate = useNavigate();
  const params = useParams();
  const dispatch = useDispatch();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [worksheet, setWorksheet] = useState({ worksheetUri: '' });
  const [results, setResults] = useState({ rows: [], fields: [] });
  const [loading, setLoading] = useState(true);
  const [sqlBody, setSqlBody] = useState(
    " select 'A' as dim, 23 as nb\n union \n select 'B' as dim, 43 as nb "
  );
  const [currentEnv, setCurrentEnv] = useState();
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [loadingDatabases, setLoadingDatabases] = useState(false);
  const [databaseOptions, setDatabaseOptions] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);
  const [columns, setColumns] = useState(null);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [tableOptions, setTableOptions] = useState([]);
  const [loadingTables, setLoadingTables] = useState(false);
  const [runningQuery, setRunningQuery] = useState(false);
  const [isEditWorksheetOpen, setIsEditWorksheetOpen] = useState(null);
  const [isDeleteWorksheetOpen, setIsDeleteWorksheetOpen] = useState(null);
  const handleEditWorksheetModalOpen = () => {
    setIsEditWorksheetOpen(true);
  };
  const handleEditWorksheetModalClose = () => {
    setIsEditWorksheetOpen(false);
  };
  const handleDeleteWorksheetModalOpen = () => {
    setIsDeleteWorksheetOpen(true);
  };
  const handleDeleteWorksheetModalClose = () => {
    setIsDeleteWorksheetOpen(false);
  };

  const fetchEnvironments = useCallback(
    async (group) => {
      setLoadingEnvs(true);
      const response = await client.query(
        listValidEnvironments({
          filter: {
            ...Defaults.selectListFilter,
            SamlGroupName: group
          }
        })
      );
      if (!response.errors) {
        setEnvironmentOptions(
          response.data.listValidEnvironments.nodes.map((e) => ({
            ...e,
            value: e.environmentUri,
            label: e.label
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingEnvs(false);
    },
    [client, dispatch]
  );

  const fetchDatabases = useCallback(
    async (environment, team) => {
      setLoadingDatabases(true);
      let ownedDatabases = [];
      let sharedWithDatabases = [];
      let response = await client.query(
        listS3DatasetsOwnedByEnvGroup({
          filter: Defaults.selectListFilter,
          environmentUri: environment.environmentUri,
          groupUri: team
        })
      );
      if (response.errors) {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      if (response.data.listS3DatasetsOwnedByEnvGroup.nodes) {
        ownedDatabases = response.data.listS3DatasetsOwnedByEnvGroup.nodes?.map(
          (d) => ({
            ...d,
            value: d.datasetUri,
            label: d.restricted.GlueDatabaseName
          })
        );
      }
      response = await client.query(
        listS3DatasetsSharedWithEnvGroup({
          environmentUri: environment.environmentUri,
          groupUri: team
        })
      );
      if (response.errors) {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      if (response.data.listS3DatasetsSharedWithEnvGroup) {
        sharedWithDatabases =
          response.data.listS3DatasetsSharedWithEnvGroup?.map((d) => ({
            value: d.datasetUri,
            label: d.sharedGlueDatabaseName,
            shareUri: d.shareUri
          }));
      }
      setDatabaseOptions(ownedDatabases.concat(sharedWithDatabases));
      setLoadingDatabases(false);
    },
    [client, dispatch]
  );
  const fetchTables = useCallback(
    async (environment, dataset) => {
      setLoadingTables(true);
      let response = '';
      if (dataset.label.includes(dataset.value + '_shared')) {
        response = await client.query(
          getSharedDatasetTables({
            datasetUri: dataset.value,
            envUri: environment.environmentUri
          })
        );
      } else {
        response = await client.query(
          listDatasetTables({
            datasetUri: dataset.value,
            filter: Defaults.selectListFilter
          })
        );
      }

      if (
        !response.errors &&
        dataset.label.includes(dataset.value + '_shared')
      ) {
        setTableOptions(
          response.data.getSharedDatasetTables.map((t) => ({
            ...t,
            value: t.tableUri,
            label: t.GlueTableName
          }))
        );
      } else if (!response.errors) {
        setTableOptions(
          response.data.getDataset.tables.nodes.map((t) => ({
            ...t,
            value: t.tableUri,
            label: t.restricted.GlueTableName
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingTables(false);
    },
    [client, dispatch]
  );
  const fetchColumns = useCallback(
    async (table, database) => {
      setLoadingColumns(true);
      let response;
      if (database?.shareUri) {
        response = await client.query(
          listSharedDatasetTableColumns({
            tableUri: table.tableUri,
            shareUri: database.shareUri,
            filter: Defaults.selectListFilter
          })
        );
      } else {
        response = await client.query(
          listDatasetTableColumns({
            tableUri: table.tableUri,
            filter: Defaults.selectListFilter
          })
        );
      }

      if (!response.errors) {
        if (database?.shareUri) {
          setColumns(
            response.data.listSharedDatasetTableColumns.nodes.map((c) => ({
              ...c,
              value: c.columnUri,
              label: c.name
            }))
          );
        } else {
          setColumns(
            response.data.listDatasetTableColumns.nodes.map((c) => ({
              ...c,
              value: c.columnUri,
              label: c.name
            }))
          );
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingColumns(false);
    },
    [client, dispatch]
  );
  const saveWorksheet = useCallback(async () => {
    const response = await client.mutate(
      updateWorksheet({
        worksheetUri: worksheet.worksheetUri,
        input: {
          label: worksheet.label,
          sqlBody,
          description: worksheet.description,
          tags: worksheet.tags
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Worksheet saved', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, enqueueSnackbar, worksheet, sqlBody]);

  const runQuery = useCallback(async () => {
    try {
      setRunningQuery(true);
      const response = await client.query(
        runAthenaSqlQuery({
          sqlQuery: sqlBody,
          environmentUri: currentEnv.environmentUri,
          worksheetUri: worksheet.worksheetUri
        })
      );
      if (!response.errors) {
        const athenaResults = response.data.runAthenaSqlQuery;
        setResults({
          rows: athenaResults.rows.map((c, index) => ({ ...c, id: index })),
          columns: athenaResults.columns.map((c, index) => ({
            ...c,
            id: index
          }))
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setRunningQuery(false);
    }
  }, [client, dispatch, currentEnv, sqlBody]);

  const deleteWorksheetfunction = useCallback(async () => {
    const response = await client.mutate(
      deleteWorksheet(worksheet.worksheetUri)
    );
    if (!response.errors) {
      enqueueSnackbar('Worksheet deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/worksheets');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, enqueueSnackbar, navigate, worksheet]);

  const fetchWorksheet = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getWorksheet(params.uri));
    if (!response.errors) {
      setWorksheet(response.data.getWorksheet);
      setSqlBody(response.data.getWorksheet.sqlBody);
      setResults(response.data.getWorksheet.lastSavedQueryResult);
      fetchEnvironments(response.data.getWorksheet.SamlAdminGroupName).catch(
        (e) => dispatch({ type: SET_ERROR, error: e.message })
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, params.uri, fetchEnvironments, dispatch]);

  useEffect(() => {
    if (client) {
      fetchWorksheet().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  function handleEnvironmentChange(event) {
    setColumns([]);
    setSelectedDatabase('');
    setSelectedTable('');
    setDatabaseOptions([]);
    setTableOptions([]);
    setCurrentEnv(event.target.value);
    fetchDatabases(event.target.value, worksheet.SamlAdminGroupName).catch(
      (e) => dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  function handleDatabaseChange(event) {
    setColumns([]);
    setTableOptions([]);
    setSelectedTable('');
    setSelectedDatabase(event.target.value);
    fetchTables(currentEnv, event.target.value).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  function handleTableChange(event) {
    setColumns([]);
    setSelectedTable(event.target.value);
    fetchColumns(event.target.value, selectedDatabase).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
    setSqlBody(
      `SELECT * FROM "${selectedDatabase.label}"."${
        event.target.value.restricted
          ? event.target.value.restricted.GlueTableName
          : event.target.value.GlueTableName
      }" limit 10;`
    );
  }

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Worksheet | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          display: 'flex',
          height: '100%'
        }}
      >
        <Box
          sx={{
            display: 'flex',
            backgroundColor: 'background.paper',
            borderRight: 1,
            borderBottom: 1,
            borderColor: 'divider',
            flexDirection: 'column',
            maxWidth: '100%',
            width: 350,
            height: '100%'
          }}
        >
          <Scrollbar options={{ suppressScrollX: true }}>
            <Box sx={{ p: 2 }}>
              <Card>
                <Box sx={{ p: 2, mt: 2 }}>
                  <TextField
                    fullWidth
                    label="Environment"
                    name="environment"
                    onChange={(event) => {
                      handleEnvironmentChange(event);
                    }}
                    select
                    value={currentEnv}
                    variant="outlined"
                    InputProps={{
                      endAdornment: (
                        <>
                          {loadingEnvs ? (
                            <CircularProgress color="inherit" size={20} />
                          ) : null}
                        </>
                      )
                    }}
                  >
                    {environmentOptions.map((environment) => (
                      <MenuItem
                        key={environment.environmentUri}
                        value={environment}
                      >
                        {environment.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </Box>
                <Box sx={{ p: 2, mt: 2 }}>
                  <TextField
                    disabled
                    fullWidth
                    label="Team"
                    name="team"
                    value={worksheet ? worksheet.SamlAdminGroupName : ''}
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ p: 2 }}>
                  <TextField
                    fullWidth
                    label="Database"
                    name="database"
                    onChange={(event) => {
                      handleDatabaseChange(event);
                    }}
                    select
                    value={selectedDatabase}
                    variant="outlined"
                    InputProps={{
                      endAdornment: (
                        <>
                          {loadingDatabases ? (
                            <CircularProgress color="inherit" size={20} />
                          ) : null}
                        </>
                      )
                    }}
                  >
                    {databaseOptions.length > 0 ? (
                      databaseOptions.map((database) => (
                        <MenuItem key={database.datasetUri} value={database}>
                          {database.label}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No databases found</MenuItem>
                    )}
                  </TextField>
                </Box>
                <Box sx={{ p: 2 }}>
                  <TextField
                    fullWidth
                    label="Table"
                    name="table"
                    onChange={(event) => {
                      handleTableChange(event);
                    }}
                    select
                    value={selectedTable}
                    variant="outlined"
                    InputProps={{
                      endAdornment: (
                        <>
                          {loadingTables ? (
                            <CircularProgress color="inherit" size={20} />
                          ) : null}
                        </>
                      )
                    }}
                  >
                    {tableOptions.length > 0 ? (
                      tableOptions.map((table) => (
                        <MenuItem key={table.tableUri} value={table}>
                          {table.label}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No tables found</MenuItem>
                    )}
                  </TextField>
                </Box>
                {loadingColumns ? (
                  <CircularProgress size={15} />
                ) : (
                  <Box sx={{ p: 2 }}>
                    {columns && columns.length > 0 && (
                      <Box>
                        <Typography color="textSecondary" variant="subtitle2">
                          Columns
                        </Typography>
                        <List dense>
                          {columns.map((col) => (
                            <Box>
                              <ListItem key={col.columnUri}>
                                {col.typeName !== 'string' ? (
                                  <ListItemIcon>
                                    <CgHashtag />
                                  </ListItemIcon>
                                ) : (
                                  <ListItemIcon>
                                    <VscSymbolString />
                                  </ListItemIcon>
                                )}
                                <Typography
                                  sx={{
                                    width: '200px',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    WebkitBoxOrient: 'vertical',
                                    WebkitLineClamp: 2
                                  }}
                                >
                                  <Tooltip title={col.name}>
                                    <Typography
                                      color="textPrimary"
                                      variant="subtitle2"
                                    >
                                      {col.name.substring(0, 22)}
                                    </Typography>
                                  </Tooltip>
                                </Typography>
                              </ListItem>
                            </Box>
                          ))}
                        </List>
                      </Box>
                    )}
                  </Box>
                )}
              </Card>
            </Box>
          </Scrollbar>
        </Box>
        <Box
          sx={{
            backgroundColor: 'background.default',
            display: 'flex',
            flexDirection: 'column',
            flexGrow: 1
          }}
        >
          <Box
            sx={{
              alignItems: 'center',
              backgroundColor: 'background.paper',
              display: 'flex',
              flexShrink: 0,
              height: 68,
              p: 2
            }}
          >
            <Box>
              <Typography color="textPrimary" variant="h5">
                {worksheet.label}
              </Typography>
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            <IconButton onClick={handleEditWorksheetModalOpen}>
              <PencilAltIcon fontSize="small" />
            </IconButton>
            <IconButton onClick={saveWorksheet}>
              <SaveOutlined fontSize="small" />
            </IconButton>
            <IconButton onClick={handleDeleteWorksheetModalOpen}>
              <FaTrash size={16} />
            </IconButton>
          </Box>
          <Divider />
          <Box sx={{ p: 2 }}>
            <SQLQueryEditor sql={sqlBody} setSqlBody={setSqlBody} />
          </Box>
          <Divider />
          <Box
            sx={{
              alignItems: 'center',
              backgroundColor: 'background.paper',
              display: 'flex',
              flexShrink: 0,
              height: 68,
              p: 2
            }}
          >
            <LoadingButton
              disabled={!currentEnv?.value}
              loading={runningQuery}
              color="primary"
              onClick={runQuery}
              startIcon={<PlayArrowOutlined fontSize="small" />}
              sx={{ m: 1 }}
              variant="contained"
            >
              Run Query
            </LoadingButton>
          </Box>
          <Divider />
          <Box sx={{ p: 2 }}>
            <WorksheetResult results={results} loading={runningQuery} />
          </Box>
        </Box>
      </Box>
      {worksheet && isEditWorksheetOpen && (
        <WorksheetEditFormModal
          worksheet={worksheet}
          onApply={handleEditWorksheetModalClose}
          onClose={handleEditWorksheetModalClose}
          reload={fetchWorksheet}
          open={isEditWorksheetOpen}
        />
      )}
      {worksheet && isDeleteWorksheetOpen && (
        <DeleteObjectWithFrictionModal
          objectName={worksheet.label}
          onApply={handleDeleteWorksheetModalClose}
          onClose={handleDeleteWorksheetModalClose}
          open={isDeleteWorksheetOpen}
          deleteFunction={deleteWorksheetfunction}
          isAWSResource={false}
        />
      )}
    </>
  );
};

export default WorksheetView;
