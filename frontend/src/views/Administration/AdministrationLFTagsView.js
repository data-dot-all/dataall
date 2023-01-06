import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as BsIcons from 'react-icons/bs';
import {
  Box,
  Card,
  Button,
  CardHeader,
  Divider,
  Grid,
  InputAdornment,
  Table,
  Chip,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import {
    GroupAddOutlined
  } from '@mui/icons-material';
import CircularProgress from '@mui/material/CircularProgress';
import { DeleteOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { useTheme } from '@mui/styles';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import Pager from '../../components/Pager';
import listTenantLFTags from '../../api/LFTags/listTenantLFTags';
import LFTagAddForm from './LFTagAddForm';
import { useSnackbar } from 'notistack';
import { HiUserRemove } from 'react-icons/hi';
import removeLFTag from '../../api/LFTags/removeLFTag';

function LFTagRow({ tag, fetchLFTags }) {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const dispatch = useDispatch();
  console.log(tag)
  const removeTag = async (tagUri) => {
    try {
      const response = await client.mutate(
        removeLFTag({
          lftagUri: tagUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('LF Tag removed', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        fetchLFTags();
        // if (fetchLFTags) {
        //   fetchLFTags();
        // }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };
  return (
    <TableRow hover>
      <TableCell>{tag.LFTagKey} </TableCell>
      <TableCell>
        {tag.LFTagValues && tag.LFTagValues.length > 0 ?  
          tag.LFTagValues?.map((tag) => (
            <Chip
              sx={{ mr: 0.5, mb: 0.5 }}
              key={tag}
              label={tag}
              variant="outlined"
            />
          ))
          : 
          <Chip
            sx={{ mr: 0.5, mb: 0.5 }}
            key={'-'}
            label={'-'}
            variant="outlined"
          />
        }
      </TableCell>
      <TableCell>{tag.team && tag.team.length > 0 ? tag.team : ['-']} </TableCell>
        <LoadingButton onClick={() => removeTag(tag.lftagUri)}>
            <DeleteOutlined fontSize="small" />
        </LoadingButton>
    </TableRow>
  );
}

LFTagRow.propTypes = {
  tag: PropTypes.any,
  fetchLFTags: PropTypes.func.isRequired
};

const LFTagsView = () => {
  const client = useClient();
  const dispatch = useDispatch();
  const [lftags, setLFTags] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [isAddLFTagModalOpen, setIsAddLFTagModalOpen] = useState(false);
  const handleAddLFTagModalOpen = () => {
    setIsAddLFTagModalOpen(true);
  };
  const handleAddLFTagModalClose = () => {
    setIsAddLFTagModalOpen(false);
  };
  const fetchLFTags = useCallback(async () => {
    try {
      const response = await client.query(listTenantLFTags(filter));
      if (!response.errors) {
        setLFTags(response.data.listTenantLFTags);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchLFTags().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= lftags.pages && value !== lftags.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchLFTags().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchLFTags, dispatch]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchLFTags} />}
          title={
            <Box>
              <BsIcons.BsPeople style={{ marginRight: '10px' }} /> Tenant LF Tags
            </Box>
          }
        />
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flexWrap: 'wrap',
            m: -1,
            p: 2
          }}
        >
        <Grid item md={10} sm={6} xs={12}>
            <Box
              sx={{
                m: 1,
                maxWidth: '100%',
                width: 500
              }}
            >
              <TextField
                fullWidth
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
                onChange={handleInputChange}
                onKeyUp={handleInputKeyup}
                placeholder="Search"
                value={inputValue}
                variant="outlined"
              />
            </Box>
          </Grid>
          <Grid item md={2} sm={6} xs={12}>
            <Button
              color="primary"
              startIcon={<GroupAddOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={handleAddLFTagModalOpen}
              variant="contained"
            >
              Add New Global LF Tag
            </Button>
            {isAddLFTagModalOpen && (
              <LFTagAddForm
                open
                reloadTags={fetchLFTags}
                onClose={handleAddLFTagModalClose}
              />
            )}
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Values</TableCell>
                  <TableCell>Teams with Access</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {lftags.nodes.length > 0 ? (
                    lftags.nodes.map((tag) => (
                      <LFTagRow tag={tag} fetchLFTag={fetchLFTags} />
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No LF Tags Created</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {!loading && lftags.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={lftags}
                onChange={handlePageChange}
              />
            )}
          </Box>
        </Scrollbar>
      </Card>
    </Box>
  );
};

LFTagsView.propTypes = {};

export default LFTagsView;
