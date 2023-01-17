import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Box, Card,
  Dialog,
  Divider,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import Checkbox from '@mui/material/Checkbox';
import {Add, SyncAlt} from '@mui/icons-material';
import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import Scrollbar from '../../components/Scrollbar';
import Pager from '../../components/Pager';
import * as Defaults from '../../components/defaults';
import { PagedResponseDefault } from '../../components/defaults';
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

  const fetchShareItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareObject({
        shareUri: params.uri,
        filter: {
          ...filter,
          isShared: true,
          isRevokable: true
        }
      })
    );
    if (!response.errors) {
      setRows(
          response.data.getShareObject.items.map((item) => ({
            id: item.shareItemUri,
            name: item.itemName,
            type: item.itemType,
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
        shareUri: share.shareUri,
        revokedItemUris: selectionModel
      })
    );
    if (!response.errors) {
      enqueueSnackbar('All items if share request revoked', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
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
    { field: 'name', headerName: 'Name', width: 400, editable: false },
    { field: 'type', headerName: 'Type', width: 400, editable: false },
    { field: 'status', headerName: 'Status', width: 400, editable: false },
  ];

  return (
    <Box>
      <Card sx={{ height: 800, width: '100%' }}>
        {rows.length > 0 && (
          <DataGrid
            rows={rows}
            columns={header}
            pageSize={10}
            rowsPerPageOptions={[10]}
            checkboxSelection
            onSelectionModelChange={(newSelection) => {
              setSelectionModel(newSelection.selectionModel);
            }}
            selectionModel={selectionModel}
          />
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
            onClick={revoke()}
            startIcon={<SyncAlt fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            Revoke Selected Items
          </LoadingButton>
        </Box>
    </Box>
  );
};

RevokeShareItemsModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};

export default RevokeShareItemsModal;
