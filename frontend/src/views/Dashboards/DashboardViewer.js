import { createRef, useEffect, useState } from 'react';
import * as ReactIf from 'react-if';
import { Box, Button, CircularProgress } from '@material-ui/core';
import { FaExternalLinkAlt } from 'react-icons/all';
import PropTypes from 'prop-types';
import getReaderSession from '../../api/Dashboard/getDashboardReaderSession';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';

const QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

const DashboardViewer = ({ dashboard }) => {
  const dispatch = useDispatch();
  const client = useClient();
  const [dashboardRef] = useState(createRef());
  const [sessionUrl, setSessionUrl] = useState(null);

  const fetchReaderSessionUrl = async () => {
    const response = await client.query(getReaderSession(dashboard.dashboardUri));
    if (!response.errors) {
      setSessionUrl(response.data.getReaderSession);
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
  };

  useEffect(() => {
    if (client && !sessionUrl) {
      fetchReaderSessionUrl().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  if (!sessionUrl) {
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
              View in Quicksight
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
export default DashboardViewer;
