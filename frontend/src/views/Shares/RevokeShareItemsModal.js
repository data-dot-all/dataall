import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Box,
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
import { Add } from '@mui/icons-material';
import { useCallback, useEffect, useState } from 'react';
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

const RevokeShareItemsModal = (props) => {
  const client = useClient();
  const { share, onApply, onClose, open, reloadSharedItems, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [sharedItems, setSharedItems] = useState(PagedResponseDefault);
  const [revoking, setRevoking] = useState(false);
  const dispatch = useDispatch();
  const params = useParams();
  const [loading, setLoading] = useState(true);

  const fetchShareItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getShareObject({
        shareUri: params.uri,
        filter: {
          ...filter,
          isShared: false
        }
      })
    );
    if (!response.errors) {
      setSharedItems({ ...response.data.getShareObject.items });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, filter]);

  const revoke = async () => {
    setRevoking(true);
    const response = await client.mutate(
      revokeItemsShareObject({
        shareUri: share.shareUri,
        revokedItemUris: ['']
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
    setRevoking(false);
  };

  const handlePageChange = async (event, value) => {
    if (value <= sharedItems.pages && value !== sharedItems.page) {
      await setFilter({ ...filter, isShared: true, page: value });
    }
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

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Revoke items from share object {share.dataset.datasetName}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          {
            "After selecting items click on revoke to revoke access!"
          }
        </Typography>
        <Divider />
        <Box sx={{ p: 3 }} />
        {!loading && sharedItems && sharedItems.nodes.length <= 0 ? (
          <Typography color="textPrimary" variant="subtitle2">
            No items to revoke.
          </Typography>
        ) : (
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Action</TableCell>
                  </TableRow>
                </TableHead>
                {loading ? (
                  <CircularProgress sx={{ mt: 1 }} size={20} />
                ) : (
                  <TableBody>
                    {sharedItems.nodes.length > 0 &&
                      sharedItems.nodes.map((item) => (
                        <TableRow hover key={item.itemUri}>
                          <TableCell>
                            {item.itemType === 'Table' ? 'Table' : 'Folder'}
                          </TableCell>
                          <TableCell>{item.itemName}</TableCell>
                          <TableCell>
                            <Checkbox name="Revoke" />
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                )}
              </Table>
              <Pager
                mgTop={2}
                mgBottom={2}
                items={sharedItems}
                onChange={handlePageChange}
              />
            </Box>
          </Scrollbar>
        )}
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
