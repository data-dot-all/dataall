import { Box, Button, CircularProgress } from '@mui/material';
import PropTypes from 'prop-types';
import { createRef, useCallback, useEffect, useState } from 'react';
import { FaExternalLinkAlt } from 'react-icons/fa';
import * as ReactIf from 'react-if';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getReaderSession } from '../services';

const QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

export const DashboardViewer = ({ dashboard }) => {
  const dispatch = useDispatch();
  const client = useClient();
  const [dashboardRef] = useState(createRef());
  const [sessionUrl, setSessionUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchReaderSessionUrl = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getReaderSession(dashboard.dashboardUri)
    );
    if (!response.errors) {
      // the API operation provides the URL with an auth_code value that enables one (and only one) sign-on to a user session
      // Auth_code is consumed by the embedDashboard so subsequent opening in the new tab will fail. We are removing
      // the code from the url (part after '?') used by the button because the user session is already authenticated.
      setSessionUrl(response.data.getReaderSession.split('?')[0]);
      const options = {
        url: response.data.getReaderSession,
        scrolling: 'no',
        height: '700px',
        width: '100%',
        locale: 'en-US',
        footerPaddingEnabled: true,
        sheetTabsDisabled: false,
        printEnabled: false,
        maximize: true,
        container: dashboardRef.current
      };
      QuickSightEmbedding.embedDashboard(options);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, dashboard, dashboardRef]);

  useEffect(() => {
    if (client && !sessionUrl) {
      fetchReaderSessionUrl().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchReaderSessionUrl, sessionUrl]);

  if (!sessionUrl && !loading) {
    return null;
  }
  if (loading) {
    return <CircularProgress />;
  }
  return (
    <div>
      <ReactIf.If condition={sessionUrl}>
        <ReactIf.Then>
          <Box sx={{ mb: 3 }}>
            <Button
              color="primary"
              component="a"
              href={sessionUrl}
              target="_blank"
              rel="noreferrer"
              startIcon={<FaExternalLinkAlt size={15} />}
              variant="outlined"
            >
              View in new tab
            </Button>
          </Box>
          <div ref={dashboardRef} />
        </ReactIf.Then>
      </ReactIf.If>
    </div>
  );
};

DashboardViewer.propTypes = {
  dashboard: PropTypes.object.isRequired
};
