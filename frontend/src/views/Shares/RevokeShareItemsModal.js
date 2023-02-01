import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Box, Card,
  Dialog,
  Divider,
  IconButton,
  Typography
} from '@mui/material';
import {Add, SyncAlt} from '@mui/icons-material';
import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import getShareObject from '../../api/ShareObject/getShareObject';
import revokeItemsShareObject from '../../api/ShareObject/revokeItemsShareObject';
import {LoadingButton} from "@mui/lab";
import {DataGrid} from "@mui/x-data-grid";

const RevokeShareItemsModal = (props) => {
  const client = useClient();
  const { share, onApply, onClose, open, reloadSharedItems, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [rows, setRows] = useState([]);
  const dispatch = useDispatch();
  const params = useParams();
  const [loading, setLoading] = useState(true);
  const [selectionModel, setSelectionModel] = useState([]);
  const [pageSize, setPageSize] = useState(5);

  const fetchShareItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareObject({
        shareUri: params.uri,
        filter: {
          ...filter,
          pageSize: 1000,
          isShared: true,
          isRevokable: true
        }
      })
    );
    if (!response.errors) {
      setRows(
          response.data.getShareObject.items.nodes.map((item) => ({
            id: item.shareItemUri,
            name: item.itemName,
            type: item.itemType == "StorageLocation"? "Folder": "Table",
            status: item.status
          }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, filter]);


  const revoke = async () => {
    setLoading(true);
    const response = await client.mutate(
      revokeItemsShareObject({
        input: {
          shareUri: share.shareUri,
          revokedItemUris: selectionModel
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Items revoked', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchShareItems();
      reloadSharedItems(true);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
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
    { field: 'status', headerName: 'Status', width: 300, editable: false },
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
          Revoke access to items from share object {share.dataset.datasetName}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          {
            "After selecting the items that you want to revoke, click on Revoke Selected Items"
          }
        </Typography>
        <Divider />
      <Box sx={{ p: 3 }} />
        <Card sx={{height: 400, width: '100%' }}>
          {!loading && rows.length > 0 ? (
            <DataGrid
              rows={rows}
              columns={header}
              pageSize={pageSize}
              rowsPerPageOptions={[5,10,20]}
              onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              checkboxSelection
              onSelectionModelChange={(newSelection) => {
                setSelectionModel(newSelection);
              }}
              selectionModel={selectionModel}
            />
          ) : (
            <Typography color="textPrimary" variant="subtitle2">
              No items to revoke.
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
              onClick={revoke}
              startIcon={<SyncAlt fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Revoke Selected Items
            </LoadingButton>
        </Box>
      </Box>
    </Dialog>
  );
};

RevokeShareItemsModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadSharedItems: PropTypes.func,
  open: PropTypes.bool.isRequired
};

export default RevokeShareItemsModal;
