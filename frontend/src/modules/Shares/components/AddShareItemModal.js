import { Add } from '@mui/icons-material';
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
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Defaults, Pager, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { addSharedItem, getShareObject } from '../services';
import { generateShareItemLabel } from 'utils';

export const AddShareItemModal = (props) => {
  const client = useClient();
  const { share, onApply, onClose, open, reloadSharedItems, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [filter, setFilter] = useState(Defaults.filter);
  const [sharedItems, setSharedItems] = useState(Defaults.pagedResponse);
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

  const addItemToShareObject = useCallback(
    async (item) => {
      const response = await client.mutate(
        addSharedItem({
          shareUri: share.shareUri,
          input: {
            itemUri: item.itemUri,
            itemType: item.itemType
          }
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Item added', {
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
    },
    [
      client,
      dispatch,
      fetchShareItems,
      reloadSharedItems,
      enqueueSnackbar,
      share.shareUri
    ]
  );

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
          Add new item to share object {share.dataset.datasetName}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          {
            "After adding an item, share object will be in draft status. Don't forget to submit your request !"
          }
        </Typography>
        <Divider />
        <Box sx={{ p: 3 }} />
        {!loading && sharedItems && sharedItems.nodes.length <= 0 ? (
          <Typography color="textPrimary" variant="subtitle2">
            No items to add.
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
                            {generateShareItemLabel(item.itemType)}
                          </TableCell>
                          <TableCell>{item.itemName}</TableCell>
                          <TableCell>
                            <IconButton
                              onClick={() => addItemToShareObject(item)}
                            >
                              <Add fontSize="small" />
                            </IconButton>
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

AddShareItemModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadSharedItems: PropTypes.func,
  open: PropTypes.bool.isRequired
};
