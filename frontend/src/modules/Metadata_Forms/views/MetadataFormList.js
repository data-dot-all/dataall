import {
  Box,
  Breadcrumbs,
  Button,
  Container,
  Grid,
  Link,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink } from 'react-router-dom';
import {
  ChevronRightIcon,
  Defaults,
  Pager,
  PlusIcon,
  SearchInput,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { fetchEnums, useClient } from 'services';
import { listUserMetadataForms } from '../services';
import { MetadataFormListItem, CreateMetadataFormModal } from '../components';

function MetadataFormsListPageHeader(props) {
  const { onCreate, visibilityDict, hasManagePermissions } = props;
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isOpeningModal, setIsOpeningModal] = useState(false);

  const handleOpenModal = () => {
    setShowCreateModal(true);
    setIsOpeningModal(true);
  };
  const handleCloseModal = () => {
    setShowCreateModal(false);
  };

  return (
    <Grid
      alignItems="center"
      container
      justifyContent="space-between"
      spacing={3}
    >
      {showCreateModal && (
        <CreateMetadataFormModal
          onApply={() => {
            handleCloseModal();
            onCreate();
          }}
          onClose={handleCloseModal}
          open={showCreateModal}
          visibilityDict={visibilityDict}
          stopLoader={() => setIsOpeningModal(false)}
        ></CreateMetadataFormModal>
      )}
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Metadata Forms
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Typography color="textPrimary" variant="subtitle2">
            Discover
          </Typography>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/metadata-forms"
            variant="subtitle2"
          >
            Metadata Forms
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        {hasManagePermissions && (
          <Box sx={{ m: -1 }}>
            <Button
              color="primary"
              startIcon={
                isOpeningModal ? (
                  <CircularProgress size={20} />
                ) : (
                  <PlusIcon fontSize="small" />
                )
              }
              sx={{ m: 1 }}
              variant="contained"
              onClick={handleOpenModal}
            >
              New Metadata Form
            </Button>
          </Box>
        )}
      </Grid>
    </Grid>
  );
}

const MetadataFormsList = () => {
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const { settings } = useSettings();
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [visibilityDict, setVisibilityDict] = useState({});
  const [hasManagePermissions, setHasManagePermissions] = useState(false);

  const client = useClient();

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(listUserMetadataForms(filter));
    if (!response.errors) {
      setItems(response.data.listUserMetadataForms);
      setHasManagePermissions(
        response.data.listUserMetadataForms.hasTenantPermissions
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, search_input: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      setFilter({ page: 1, search_input: event.target.value });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const fetchVisibilityOptions = async () => {
    try {
      const enumVisibilityOptions = await fetchEnums(client, [
        'MetadataFormVisibility'
      ]);
      if (enumVisibilityOptions['MetadataFormVisibility'].length > 0) {
        let tmpVisibilityDict = {};
        enumVisibilityOptions['MetadataFormVisibility'].map((x) => {
          tmpVisibilityDict[x.name] = x.value;
        });
        setVisibilityDict(tmpVisibilityDict);
      } else {
        const error = 'Could not fetch visibility options';
        dispatch({ type: SET_ERROR, error });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchVisibilityOptions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

  return (
    <>
      <Helmet>
        <title>Metadata Forms| data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <MetadataFormsListPageHeader
            onCreate={fetchItems}
            visibilityDict={visibilityDict}
            hasManagePermissions={hasManagePermissions}
          />
          <Box sx={{ mt: 3 }}>
            <SearchInput
              onChange={handleInputChange}
              onKeyUp={handleInputKeyup}
              value={inputValue}
            />
          </Box>

          <Box
            sx={{
              flexGrow: 1,
              mt: 3
            }}
          >
            {loading ? (
              <CircularProgress />
            ) : (
              <Box>
                <Grid container spacing={3}>
                  {items.nodes.map((node) => (
                    <MetadataFormListItem
                      metadata_form={node}
                      visibilityDict={visibilityDict}
                    />
                  ))}
                </Grid>

                <Pager items={items} onChange={handlePageChange} />
              </Box>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default MetadataFormsList;
