import { SyncAlt } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { Box, Card, Dialog, Divider, Typography } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { useSnackbar } from 'notistack';
import { verifyDatasetShareObjects } from '../services';

export const ShareObjectSelectorModal = (props) => {
  const client = useClient();
  const { shares, dataset, onApply, onClose, open, ...other } = props;
  const [rows, setRows] = useState([]);
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [selectionModel, setSelectionModel] = useState([]);
  const [pageSize, setPageSize] = useState(5);
  const { enqueueSnackbar } = useSnackbar();

  const verify = async (selectionModel) => {
    setLoading(true);
    const response = await client.mutate(
      verifyDatasetShareObjects({
        input: {
          datasetUri: dataset.datasetUri,
          shareUris: selectionModel
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Share Object Verification Started.', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      onClose();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  useEffect(() => {
    const filteredShares = shares.filter(
      (share) => share.statistics.sharedItems > 0
    );
    setRows(
      filteredShares.map((share) => ({
        id: share.shareUri,
        requestOwner: share.principal.SamlGroupName,
        IAMRole: share.principal.principalRoleName,
        status: share.status
      }))
    );
  }, [client, dispatch, shares]);

  if (!shares) {
    return null;
  }
  if (!rows) {
    return null;
  }
  const header = [
    {
      field: 'requestOwner',
      headerName: 'requestOwner',
      width: 200,
      editable: false
    },
    { field: 'IAMRole', headerName: 'IAMRole', width: 300, editable: false },
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
          Verify health status of all items for selected share object(s) from
          dataset {dataset.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          After selecting the items, click Verify Selected Shares
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
              No share objects to verify.
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
            onClick={() => verify(selectionModel)}
            startIcon={<SyncAlt fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            Verify Selected Shares
          </LoadingButton>
        </Box>
      </Box>
    </Dialog>
  );
};

ShareObjectSelectorModal.propTypes = {
  shares: PropTypes.array.isRequired,
  dataset: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};
