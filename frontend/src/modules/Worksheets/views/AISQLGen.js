import {
  PlayArrowOutlined,
  SaveOutlined,
  WarningAmber,
  ContentCopy
} from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CircularProgress,
  Divider,
  IconButton,
  Button,
  MenuItem,
  TextField,
  Typography,
  Autocomplete,
  Chip
} from '@mui/material';

import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { FaTrash } from 'react-icons/fa';
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
  listS3DatasetsOwnedByEnvGroup,
  listValidEnvironments,
  useClient
} from 'services';
import {
  deleteWorksheet,
  getWorksheet,
  runAthenaSqlQuery,
  textToSQL,
  updateWorksheet,
  listS3DatasetsSharedWithEnvGroup
} from '../services';
import {
  SQLQueryEditor,
  WorksheetEditFormModal,
  WorksheetResult
} from '../components';

const AISQLGenerator = () => {
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
  const [invoking, setInvoking] = useState(false);
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [loadingDatabases, setLoadingDatabases] = useState(false);
  const [databaseOptions, setDatabaseOptions] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedTables, setSelectedTables] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [tableOptions, setTableOptions] = useState([]);
  const [failedQueries, setFailedQueries] = useState([]);
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
            label: d.GlueDatabaseName
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
            label: t.GlueTableName
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
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

  const handleSubmit = async () => {
    setInvoking(true);
    setSqlBody('');
    const selectTablesString = selectedTables.join(' ');
    const oldPrompt = prompt;
    if (failedQueries.length !== 0) {
      setPrompt((currentPrompt) => currentPrompt + failedQueries.join('\n'));
    }

    const queryObject = textToSQL({
      prompt: prompt,
      environmentUri: currentEnv.environmentUri,
      worksheetUri: worksheet.worksheetUri,
      datasetUri: selectedDatabase.value,
      tableNames: selectedTables
    });
    setPrompt(oldPrompt);
    const response = await client.query(queryObject);
    const message = response.data.textToSQL;
    if (message.split(':')[0] === 'Error') {
      dispatch({ type: SET_ERROR, error: message.split(':')[1] });
    } else {
      setSqlBody(response.data.textToSQL.response);
    }
    setInvoking(false);
  };

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
        const error = `${sqlBody} gave the following error: ${response.errors[0].message}`;

        setFailedQueries((prevList) => [...prevList, error]);
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
    setSelectedDatabase('');
    setSelectedTables([]);
    setFailedQueries([]);
    setDatabaseOptions([]);
    setTableOptions([]);
    setPrompt('');
    setSqlBody('');
    setCurrentEnv(event.target.value);
    fetchDatabases(event.target.value, worksheet.SamlAdminGroupName).catch(
      (e) => dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  function handlePromptChange(prompt) {
    setPrompt(prompt);
    setFailedQueries([]);
  }

  function handleTablesChange(newValue) {
    setSelectedTables(newValue);
    setFailedQueries([]);
    setPrompt('');
  }

  function handleDatabaseChange(event) {
    setTableOptions([]);
    setFailedQueries([]);
    setSelectedTables([]);
    setPrompt('');

    setSelectedDatabase(event.target.value);
    fetchTables(currentEnv, event.target.value).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(sqlBody).then(() => {
      enqueueSnackbar('Text copied to clipboard', {
        variant: 'success',
        anchorOrigin: {
          vertical: 'top',
          horizontal: 'right'
        }
      });
    });
  };

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
                  <Autocomplete
                    multiple
                    options={tableOptions.map((t) => t.GlueTableName)}
                    value={selectedTables}
                    onChange={(_, newValue) => handleTablesChange(newValue)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        variant="outlined"
                        label="Select Tables"
                        placeholder="Tables"
                      />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          variant="outlined"
                          label={option}
                          {...getTagProps({ index })}
                        />
                      ))
                    }
                    disabled={!selectedDatabase}
                    fullWidth
                    margin="normal"
                  />
                </Box>
                <Box sx={{ p: 2 }}>
                  <TextField
                    fullWidth
                    label="Prompt"
                    multiline
                    rows={4}
                    value={prompt}
                    onChange={(e) => handlePromptChange(e.target.value)}
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ p: 2 }}>
                  <LoadingButton
                    loading={invoking}
                    variant="contained"
                    onClick={handleSubmit}
                    fullWidth
                  >
                    {failedQueries.length === 0
                      ? 'Generate SQL'
                      : 'Retry SQL Generation'}
                  </LoadingButton>
                </Box>
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
              p: 2,
              justifyContent: 'space-between'
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
              Run SQL
            </LoadingButton>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Button
                startIcon={<ContentCopy />}
                onClick={handleCopyToClipboard}
                variant="outlined"
                size="small"
              >
                Copy to Clipboard
              </Button>
            </Box>

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: 'background.paper',
                borderRadius: 1,
                justifyContent: 'space-between',
                px: 2,
                py: 1,
                ml: 2
              }}
            >
              <WarningAmber color="warning" sx={{ mr: 1 }} />
              <Typography variant="body2" color="warning.dark">
                Carefully review this AI-generated response for accuracy
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              alignItems: 'center',
              backgroundColor: 'background.paper',
              display: 'flex',
              flexShrink: 0,
              height: 30,
              p: 2
            }}
          ></Box>

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

export default AISQLGenerator;
