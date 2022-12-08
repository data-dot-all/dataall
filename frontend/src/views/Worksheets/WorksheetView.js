import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
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
import { useNavigate, useParams } from 'react-router-dom';
import { CgHashtag } from 'react-icons/cg';
import { FaTrash } from 'react-icons/fa';
import { VscSymbolString } from 'react-icons/vsc';
import { PlayArrowOutlined, SaveOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { useSnackbar } from 'notistack';
import { useDispatch } from '../../store';
import getWorksheet from '../../api/Worksheet/getWorksheet';
import updateWorksheet from '../../api/Worksheet/updateWorksheet';
import runAthenaSqlQuery from '../../api/Worksheet/runAthenaSqlQuery';
import deleteWorksheet from '../../api/Worksheet/deleteWorksheet';
import useClient from '../../hooks/useClient';
import listEnvironments from '../../api/Environment/listEnvironments';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import { SET_ERROR } from '../../store/errorReducer';
import listDatasetsOwnedByEnvGroup from '../../api/Environment/listDatasetsOwnedByEnvGroup';
import listDatasetTables from '../../api/Dataset/listDatasetTables';
import getSharedDatasetTables from '../../api/Dataset/getSharedDatasetTables';
import listDatasetTableColumns from '../../api/DatasetTable/listDatasetTableColumns';
import searchEnvironmentDataItems from '../../api/Environment/listDatasetsPublishedInEnvironment';
import PencilAltIcon from '../../icons/PencilAlt';
import Scrollbar from '../../components/Scrollbar';
import SQLQueryEditor from './SQLQueryEditor';
import WorksheetResult from './WorksheetResult';
import WorksheetEditFormModal from './WorksheetEditFormModal';
import DeleteObjectWithFrictionModal from '../../components/DeleteObjectWithFrictionModal';
import * as Defaults from '../../components/defaults';



const WorksheetView = () => {
  const navigate = useNavigate();
  const params = useParams();
  const dispatch = useDispatch();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [groupOptions, setGroupOptions] = useState([]);
  const [worksheet, setWorksheet] = useState({ worksheetUri: '' });
  const [results, setResults] = useState({ rows: [], fields: [] });
  const [loading, setLoading] = useState(true);
  const [sqlBody, setSqlBody] = useState(
    " select 'A' as dim, 23 as nb\n union \n select 'B' as dim, 43 as nb "
  );
  const [currentEnv, setCurrentEnv] = useState();
  const [currentTeam, setCurrentTeam] = useState();
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

  const fetchEnvironments = useCallback(async () => {
    setLoadingEnvs(true);
    const response = await client.query(
      listEnvironments({ filter: Defaults.DefaultFilter })
    );
    if (!response.errors) {
      setEnvironmentOptions(
        response.data.listEnvironments.nodes.map((e) => ({
          ...e,
          value: e.environmentUri,
          label: e.label
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoadingEnvs(false);
  }, [client, dispatch]);

  const fetchGroups = async (environmentUri) => {
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.SelectListFilter,
          environmentUri
        })
      );
      if (!response.errors) {
        setGroupOptions(
          response.data.listEnvironmentGroups.nodes.map((g) => ({
            value: g.groupUri,
            label: g.groupUri
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  const fetchDatabases = useCallback(
    async (environment, team) => {
      setLoadingDatabases(true);
      let ownedDatabases = [];
      let sharedWithDatabases = [];
      let response = await client.query(
        listDatasetsOwnedByEnvGroup({
          filter: { 
            term: '', 
            page: 1, 
            pageSize: 10000
          },
          environmentUri: environment.environmentUri,
          groupUri: team
        }));
      if (response.errors) {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      if (response.data.listDatasetsOwnedByEnvGroup.nodes) {
        ownedDatabases =
          response.data.listDatasetsOwnedByEnvGroup.nodes?.map((d) => ({
            ...d,
            value: d.datasetUri,
            label: d.GlueDatabaseName
          }));
      }
      response = await client.query(
        searchEnvironmentDataItems({
          environmentUri: environment.environmentUri,
          filter: {
            page: 1,
            pageSize: 10000,
            term: '',
            itemTypes: 'DatasetTable'
          }
        })
      );
      if (response.errors) {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      if (response.data.searchEnvironmentDataItems.nodes) {
        sharedWithDatabases =
          response.data.searchEnvironmentDataItems.nodes.map((d) => ({
            datasetUri: d.datasetUri,
            value: d.datasetUri,
            label: `${d.GlueDatabaseName}_shared_${d.shareUri}`,
            GlueDatabaseName: `${d.GlueDatabaseName}_shared_${d.shareUri}`.substring(0,254),
            environmentUri: d.environmentUri
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
      let response = ""
      if (dataset.GlueDatabaseName.includes(dataset.datasetUri+"_shared_")){
        response = await client.query(
          getSharedDatasetTables({
            datasetUri: dataset.datasetUri,
            envUri: environment.environmentUri
          })
        );
      } else{
        response = await client.query(
          listDatasetTables({
            datasetUri: dataset.datasetUri,
            filter: Defaults.SelectListFilter
          })
        );
      }

      if (!response.errors && dataset.GlueDatabaseName.includes(dataset.datasetUri+"_shared_")) {
        setTableOptions(
          response.data.getSharedDatasetTables.map((t) => (
            {
              ...t,
              value: t.tableUri,
              label: t.GlueTableName
            }
          ))
        );
      } else if(!response.errors){
        setTableOptions(
          response.data.getDataset.tables.nodes.map((t) => (
            {
              ...t,
              value: t.tableUri,
              label: t.GlueTableName
            }
          ))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingTables(false);
    },
    [client, dispatch]
  );
  const fetchColumns = useCallback(
    async (table) => {
      setLoadingColumns(true);
      const response = await client.query(
        listDatasetTableColumns({
          tableUri: table.tableUri,
          filter: Defaults.SelectListFilter
        })
      );
      if (!response.errors) {
        setColumns(
          response.data.listDatasetTableColumns.nodes.map((c) => ({
            ...c,
            value: c.columnUri,
            label: c.name
          }))
        );
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
            environmentUri:currentEnv.environmentUri,
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
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, params.uri, dispatch]);
  useEffect(() => {
    if (client) {
      fetchWorksheet().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchWorksheet, fetchEnvironments, dispatch]);

  function handleEnvironmentChange(event) {
    setColumns([]);
    setSelectedDatabase('');
    setSelectedTable('');
    setDatabaseOptions([]);
    setTableOptions([]);
    setCurrentTeam('');
    setCurrentEnv(event.target.value);
    fetchGroups(
        event.target.value.environmentUri
      ).catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
  }

  function handleTeamChange(event) {
    setColumns([]);
    setSelectedDatabase('');
    setSelectedTable('');
    setDatabaseOptions([]);
    setTableOptions([]);
    setCurrentTeam(event.target.value);
    fetchDatabases(currentEnv, event.target.value).catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
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
    fetchColumns(event.target.value).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
    setSqlBody(
      `SELECT * FROM "${selectedDatabase.GlueDatabaseName}"."${event.target.value.GlueTableName}" limit 10;`
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
                    fullWidth
                    label="Team"
                    name="team"
                    onChange={(event) => {
                      handleTeamChange(event);
                    }}
                    select
                    value={currentTeam}
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
                    {groupOptions.map((group) => (
                      <MenuItem
                        key={group.value} value={group.value}
                      >
                        {group.label}
                      </MenuItem>
                    ))}
                  </TextField>
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
                          {table.GlueTableName}
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
