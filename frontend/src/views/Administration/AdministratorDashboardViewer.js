import { createRef, useCallback, useEffect, useState } from 'react';
import * as ReactIf from 'react-if';
import { Box, Button, CircularProgress } from '@mui/material';
import { FaExternalLinkAlt, FaCheckCircle} from 'react-icons/fa';
import getReaderSession from '../../api/Dashboard/getDashboardReaderSession';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';


const QuickSightEmbedding = require('amazon-quicksight-embedding-sdk');

const DashboardViewer = () => {
  const dispatch = useDispatch();
  const client = useClient();
  const [dashboardRef] = useState(createRef());
  const [sessionUrl, setSessionUrl] = useState(null);
  const [qsDisabled, setQsDisabled] = useState(true);

  const enableQuicksight = async () => {
    console.log("inside enable quicksight")
  };
  const fetchReaderSessionUrl = useCallback(async () => {
    const response = await client.query(
      getReaderSession("abdcdme")
    );
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
  }, [client, dispatch, dashboardRef]);

  useEffect(() => {
    if (client && !sessionUrl) {
      fetchReaderSessionUrl().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchReaderSessionUrl, sessionUrl]);

  if (!sessionUrl) {
    return <CircularProgress />;
  }
  return (
    <div>
      <ReactIf.If condition={qsDisabled}>
        <ReactIf.Then>
          <Box sx={{ mb: 3 }}>
            <Button
              color="primary"
              startIcon={<FaCheckCircle size={15} />}
              sx={{ m: 1 }}
              variant="outlined"
              onClick={() => {
                enableQuicksight();
              }}
            >
              Enable Monitoring with Quicksight
            </Button>
          </Box>
        </ReactIf.Then>
      </ReactIf.If>
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

export default DashboardViewer;
