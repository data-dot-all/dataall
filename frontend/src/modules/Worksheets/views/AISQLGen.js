import { WarningAmber } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CircularProgress,
  MenuItem,
  TextField,
  Typography,
  Autocomplete,
  Chip
} from '@mui/material';

import React, { useState } from 'react';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { textToSQL } from '../services';

const AISQLGenerator = ({
  handleEnvironmentChange,
  loadingEnvs,
  currentEnv,
  environmentOptions,
  worksheet,
  handleDatabaseChange,
  selectedDatabase,
  loadingDatabases,
  databaseOptions,
  loadingTables,
  tableOptions,
  handleSQLChange
}) => {
  const dispatch = useDispatch();
  const client = useClient();
  const [invoking, setInvoking] = useState(false);
  const [selectedTables, setSelectedTables] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [failedQueries, setFailedQueries] = useState([]);

  const handleSubmit = async () => {
    setInvoking(true);
    handleSQLChange('');
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
      handleSQLChange(response.data.textToSQL.response);
    }
    setInvoking(false);
  };

  function handlePromptChange(prompt) {
    setPrompt(prompt);
    setFailedQueries([]);
  }

  function handleTablesChange(newValue) {
    setSelectedTables(newValue);
    setFailedQueries([]);
    setPrompt('');
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
  );
};

export default AISQLGenerator;
