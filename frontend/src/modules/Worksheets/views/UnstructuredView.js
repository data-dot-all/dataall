import {
  Box,
  Card,
  CircularProgress,
  Divider,
  IconButton,
  Button,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { SaveOutlined, WarningAmber, ContentCopy } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
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
  listValidEnvironments,
  listObjectKeys,
  useClient,
  listS3DatasetsOwnedByEnvGroup
} from 'services';
import {
  deleteWorksheet,
  getWorksheet,
  unstructuredQuery,
  updateWorksheet,
  listS3DatasetsSharedWithEnvGroup
} from '../services';
import {
  WorksheetEditFormModal,
  // WorksheetResult,
  TextDisplay
} from '../components';

const DocumentSummarizer = () => {
  const navigate = useNavigate();
  const params = useParams();
  const dispatch = useDispatch();
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [worksheet, setWorksheet] = useState({ worksheetUri: '' });
  const [loading, setLoading] = useState(true);
  const [textBody, setTextBody] = useState(
    " select 'A' as dim, 23 as nb\n union \n select 'B' as dim, 43 as nb "
  );
  const [invocing, setInvocing] = useState(false);
  const [currentEnv, setCurrentEnv] = useState();
  const [loadingEnvs, setLoadingEnvs] = useState(false);
  const [loadingDatabases, setLoadingDatabases] = useState(false);
  const [databaseOptions, setDatabaseOptions] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [keyOptions, setKeyOptions] = useState([]);
  const [selectedKey, setSelectedKey] = useState('');
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

  const fetchKeys = useCallback(
    async (environment, dataset) => {
      setLoadingKeys(true);
      const response = await client.query(
        listObjectKeys({
          datasetUri: dataset.value,
          environmentUri: environment.environmentUri,
          worksheetUri: worksheet.worksheetUri
        })
      );
      if (!response.errors) {
        const keys = response.data.listObjectKeys.objectKeys.split(' ');
        setKeyOptions(keys);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      setLoadingKeys(false);
    },
    [client, dispatch]
  );
  const saveWorksheet = useCallback(async () => {
    const response = await client.mutate(
      updateWorksheet({
        worksheetUri: worksheet.worksheetUri,
        input: {
          label: worksheet.label,
          sqlBody: textBody,
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
  }, [client, dispatch, enqueueSnackbar, worksheet, textBody]);

  const handleSubmit = async () => {
    setInvocing(true);
    const queryObject = unstructuredQuery({
      prompt: prompt,
      key: selectedKey,
      environmentUri: currentEnv.environmentUri,
      worksheetUri: worksheet.worksheetUri,
      datasetUri: selectedDatabase.value
    });
    const response = await client.query(queryObject);
    setTextBody(response.data.unstructuredQuery.response);
    setInvocing(false);
  };

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
      setTextBody(response.data.getWorksheet.sqlBody);
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
    setDatabaseOptions([]);
    setCurrentEnv(event.target.value);
    fetchDatabases(event.target.value, worksheet.SamlAdminGroupName).catch(
      (e) => dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  function handleDatabaseChange(event) {
    setSelectedDatabase(event.target.value);
    fetchKeys(currentEnv, event.target.value).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
  }

  function handleKeyChange(event) {
    setSelectedKey(event.target.value);
  }

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(textBody).then(() => {
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
                    label="Bucket"
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
                    label="Key"
                    name="key"
                    onChange={(event) => {
                      handleKeyChange(event);
                    }}
                    select
                    value={selectedKey}
                    variant="outlined"
                    InputProps={{
                      endAdornment: (
                        <>
                          {loadingKeys ? (
                            <CircularProgress color="inherit" size={20} />
                          ) : null}
                        </>
                      )
                    }}
                  >
                    {keyOptions.length > 0 ? (
                      keyOptions.map((key) => (
                        <MenuItem key={key} value={key}>
                          {key}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No keys found</MenuItem>
                    )}
                  </TextField>
                </Box>

                <Box sx={{ p: 2 }}>
                  <TextField
                    fullWidth
                    label="Prompt"
                    multiline
                    rows={4}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    variant="outlined"
                  />
                </Box>
                <Box sx={{ p: 2 }}>
                  <LoadingButton
                    loading={invocing}
                    variant="contained"
                    onClick={handleSubmit}
                    fullWidth
                    disabled={
                      !currentEnv ||
                      !selectedDatabase ||
                      !selectedKey ||
                      !prompt
                    }
                  >
                    Summarize
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
            <TextDisplay text={textBody} setSqlBody={setTextBody} />
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
              justifyContent: 'space-between' // This will push items to the edges
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: 'background.paper',
                borderRadius: 1,
                px: 2,
                py: 1
              }}
            >
              <WarningAmber color="warning" sx={{ mr: 1 }} />
              <Typography variant="body2" color="warning.dark">
                Carefully review this AI-generated response for accuracy
              </Typography>
            </Box>

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

export default DocumentSummarizer;
