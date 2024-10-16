import {
  Box,
  Card,
  CircularProgress,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { WarningAmber } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import React, { useCallback, useState } from 'react';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listObjectKeys, useClient } from 'services';
import { unstructuredQuery } from '../services';
import PropTypes from 'prop-types';

export const WorksheetDocSummarizer = ({
  handleEnvironmentChange,
  loadingEnvs,
  currentEnv,
  environmentOptions,
  worksheet,
  handleDatabaseChange,
  selectedDatabase,
  loadingDatabases,
  databaseOptions,
  handleTextChange
}) => {
  const dispatch = useDispatch();
  const client = useClient();
  const [invoking, setInvoking] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [keyOptions, setKeyOptions] = useState([]);
  const [selectedKey, setSelectedKey] = useState('');

  function handleBucketChange(event) {
    handleDatabaseChange(event.target.value);
    fetchKeys(currentEnv, event.target.value).catch((e) =>
      dispatch({ type: SET_ERROR, error: e.message })
    );
  }
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

  const handleSubmit = async () => {
    setInvoking(true);
    const queryObject = unstructuredQuery({
      prompt: prompt,
      key: selectedKey,
      environmentUri: currentEnv.environmentUri,
      worksheetUri: worksheet.worksheetUri,
      datasetUri: selectedDatabase.value
    });
    const response = await client.query(queryObject);
    handleTextChange(response.data.unstructuredQuery.response);
    setInvoking(false);
  };

  function handleKeyChange(event) {
    setSelectedKey(event.target.value);
  }

  return (
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
                  handleBucketChange(event);
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
              <Typography variant="body2" color="warning.dark">
                <WarningAmber color="warning" sx={{ mr: 1 }} />
                Carefully review this AI-generated response for accuracy
              </Typography>
            </Box>
            <Box sx={{ p: 2 }}>
              <LoadingButton
                loading={invoking}
                variant="contained"
                onClick={handleSubmit}
                fullWidth
                disabled={
                  !currentEnv || !selectedDatabase || !selectedKey || !prompt
                }
              >
                Summarize
              </LoadingButton>
            </Box>
          </Card>
        </Box>
      </Scrollbar>
    </Box>
  );
};


WorksheetDocSummarizer.propTypes = {
  handleEnvironmentChange: PropTypes.func.isRequired,
  loadingEnvs: PropTypes.bool.isRequired,
  currentEnv: PropTypes.object.isRequired,
  environmentOptions: PropTypes.array.isRequired,
  worksheet: PropTypes.object.isRequired,
  handleDatabaseChange: PropTypes.func.isRequired,
  selectedDatabase: PropTypes.object.isRequired,
  loadingDatabases: PropTypes.bool.isRequired,
  databaseOptions: PropTypes.array.isRequired,
  handleTextChange: PropTypes.func.isRequired,
};