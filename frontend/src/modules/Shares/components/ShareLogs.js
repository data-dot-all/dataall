import Editor from '@monaco-editor/react';
import { RefreshRounded } from '@mui/icons-material';
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  Grid,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { THEMES, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { getShareLogs, useClient } from 'services';

export const ShareLogs = (props) => {
  const { shareUri, onClose, open } = props;
  const { settings } = useSettings();
  const client = useClient();
  const dispatch = useDispatch();
  const [logs, setLogs] = useState(null);
  const [loading, setLoading] = useState(true);

  const getLogs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.query(getShareLogs(shareUri));
      if (response && !response.errors) {
        setLogs(response.data.getShareLogs.map((l) => l.message));
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
    setLoading(false);
  }, [client, dispatch, shareUri]);

  useEffect(() => {
    if (client && open) {
      getLogs().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, getLogs, open]);

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Box sx={{ p: 3 }}>
        <Grid container justifyContent="space-between" spacing={3}>
          <Grid item>
            <Typography color="textPrimary" gutterBottom variant="h6">
              Logs for share {shareUri}
            </Typography>
          </Grid>
          <Grid item />
          <Box sx={{ m: -1, mt: 2 }}>
            <Button
              color="primary"
              startIcon={<RefreshRounded fontSize="small" />}
              variant="outlined"
              onClick={getLogs}
            >
              Refresh
            </Button>
          </Box>
        </Grid>
        <Box sx={{ height: '35rem' }}>
          {loading ? (
            <CircularProgress />
          ) : (
            <Box>
              {logs && (
                <Box sx={{ mt: 1 }}>
                  <div
                    style={{
                      width: '100%',
                      border:
                        settings.theme === THEMES.LIGHT ? '1px solid #eee' : ''
                    }}
                  >
                    <Editor
                      value={
                        logs.length > 0
                          ? logs.join('\n')
                          : 'No logs available. Logs may take few minutes after the share is processed...'
                      }
                      options={{ minimap: { enabled: false } }}
                      theme="vs-dark"
                      inDiffEditor={false}
                      height="35rem"
                      language="text"
                      showPrintMargin
                      showGutter
                      highlightActiveLine
                      editorProps={{
                        $blockScrolling: Infinity
                      }}
                      setOptions={{
                        enableBasicAutocompletion: true,
                        enableLiveAutocompletion: true,
                        enableSnippets: true,
                        showLineNumbers: true,
                        tabSize: 2
                      }}
                    />
                  </div>
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Box>
    </Dialog>
  );
};

ShareLogs.propTypes = {
  shareUri: PropTypes.string.isRequired
};
