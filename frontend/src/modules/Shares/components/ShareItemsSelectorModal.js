import { SyncAlt } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { Box, Card, Dialog, Divider, Typography } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { getShareObject } from '../services';
import { generateShareItemLabel } from 'utils';

export const ShareItemsSelectorModal = (props) => {
  const client = useClient();
  const { share, onApply, onClose, open, submit, name, filter, ...other } =
    props;
  const [rows, setRows] = useState([]);
  const dispatch = useDispatch();
  const params = useParams();
  const [loading, setLoading] = useState(false);
  const [selectionModel, setSelectionModel] = useState([]);
  const [pageSize, setPageSize] = useState(5);

  const fetchShareItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareObject({
        shareUri: params.uri,
        filter: filter
      })
    );
    if (!response.errors) {
      setRows(
        response.data.getShareObject.items.nodes.map((item) => ({
          id: item.shareItemUri,
          name: item.itemName,
          type: generateShareItemLabel(item.itemType),
          status: item.status
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, Defaults.filter]);

  const submitting = async (shareUri, selectionModel) => {
    setLoading(true);
    await submit(shareUri, selectionModel);
    setLoading(false);
  };

  useEffect(() => {
    if (client) {
      fetchShareItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchShareItems]);

  if (!share) {
    return null;
  }
  if (!rows) {
    return null;
  }
  const header = [
    { field: 'name', headerName: 'Name', width: 200, editable: false },
    { field: 'type', headerName: 'Type', width: 300, editable: false },
    { field: 'status', headerName: 'Status', width: 300, editable: false }
  ];

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          {name} access to items from share object {share.dataset.datasetName}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          After selecting the items, click {name} on Selected Items
        </Typography>
        <Divider />
        <Box sx={{ p: 3 }} />
        <Card sx={{ height: 400, width: '100%' }}>
          {!loading && rows.length > 0 ? (
            <DataGrid
              rows={rows}
              columns={header}
              pageSize={pageSize}
              rowsPerPageOptions={[5, 10, 20]}
              onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              checkboxSelection
              onSelectionModelChange={(newSelection) => {
                setSelectionModel(newSelection);
              }}
              selectionModel={selectionModel}
            />
          ) : (
            <Typography color="textPrimary" variant="subtitle2">
              No items to {name.toLowerCase()}.
            </Typography>
          )}
        </Card>
        <Box
          sx={{
            display: 'flex',
            flex: 1,
            justifyContent: 'flex-end',
            mb: 2
          }}
        >
          <LoadingButton
            loading={loading}
            color="primary"
            onClick={() => submitting(share.shareUri, selectionModel)}
            startIcon={<SyncAlt fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            {name} Selected Items
          </LoadingButton>
        </Box>
      </Box>
    </Dialog>
  );
};

ShareItemsSelectorModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  submit: PropTypes.func.isRequired,
  name: PropTypes.string.isRequired,
  filter: PropTypes.object
};
