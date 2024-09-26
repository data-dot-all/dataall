import {
  Box,
  Card,
  CardHeader,
  CircularProgress,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useState, useCallback } from 'react';
import { FaBars } from 'react-icons/fa';
import * as ReactIf from 'react-if';
import { Scrollbar } from 'design';

import Stack from '@mui/material/Stack';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import { Download } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  useClient
} from 'services';
import {
  createWorksheetQueryResultDownloadUrl
} from '../services';
import { SET_ERROR, useDispatch } from 'globalErrors';

export const WorksheetResult = ({ results, loading, currentEnv, athenaQueryId, worksheetUri }) => {
  const [runningDownloadQuery, setRunningDownloadQuery] = useState(false);
  const [fileType, setFileType] = useState('csv');
  const client = useClient();
  const dispatch = useDispatch();

  const handleChange = (event) => {
    setFileType(event.target.value);
  };

  const downloadFile = useCallback(async () => {
    try {
      setRunningDownloadQuery(true);
      const response = await client.query(
        createWorksheetQueryResultDownloadUrl({
          fileFormat: fileType,
          environmentUri: currentEnv.environmentUri,
          athenaQueryId: athenaQueryId,
          worksheetUri: worksheetUri
        })
      );

      if (!response.errors) {
        const link = document.createElement('a');
        link.href = response.data.createWorksheetQueryResultDownloadUrl.downloadLink;
        // Append to html link element page
        document.body.appendChild(link);
        // Start download
        link.click();
        // Clean up and remove the link
        link.parentNode.removeChild(link);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setRunningDownloadQuery(false);
    }
  }, [client, dispatch, currentEnv, athenaQueryId, fileType])

  if (loading) {
    return <CircularProgress />;
  }
  if (results && results.Error) {
    return <Paper>{results.Error}</Paper>;
  }
  return (
    <ReactIf.If condition={results && results.columns}>
      <ReactIf.Then>
        <Card sx={{ maxWidth: 1140 }}>
          <CardHeader
            title={
              <Box>
                <FaBars /> Query Results
              </Box>
            }
            action={
              <>
                <Stack direction="row" spacing={2}>
                  <RadioGroup
                    row
                    aria-labelledby="demo-row-radio-buttons-group-label"
                    name="row-radio-buttons-group"
                    value={fileType}
                    onChange={handleChange}
                  >
                    <FormControlLabel value="csv" control={<Radio />} label="CSV" />
                    <FormControlLabel value="xlsx" control={<Radio />} label="XLSX" />
                  </RadioGroup>

                  <LoadingButton
                    loading={runningDownloadQuery}
                    color="primary"
                    onClick={downloadFile}
                    startIcon={<Download fontSize="small" />}
                    sx={{ m: 1 }}
                    variant="contained"
                  >
                    Download
                  </LoadingButton>
                </Stack>

              </>
            }
          />
          <Divider />
          <Scrollbar>
            <Box>
              <Table stickyHeader aria-label="sticky table">
                <TableHead>
                  <TableRow>
                    {results &&
                      results.columns &&
                      results.columns &&
                      results.columns.map((col) => (
                        <TableCell>{col.columnName}</TableCell>
                      ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results &&
                    results.rows &&
                    results.rows.map((row) => (
                      <TableRow>
                        {row.cells.map((cell) => (
                          <TableCell>{cell.value}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </Box>
          </Scrollbar>
        </Card>
      </ReactIf.Then>
    </ReactIf.If>
  );
};
WorksheetResult.propTypes = {
  results: PropTypes.object.isRequired,
  loading: PropTypes.bool.isRequired
};
