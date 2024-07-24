import { ForumOutlined, Warning } from '@mui/icons-material';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { useSnackbar } from 'notistack';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  ChevronRightIcon,
  DeleteObjectModal,
  PencilAltIcon,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { FeedComments } from 'modules/Shared';
import {
  getRedshiftDatasetTable,
  deleteRedshiftDatasetTable
} from '../services';
import { TableColumns, TableOverview } from '../components';

const tabs = [
  { label: 'Overview', value: 'overview' },
  { label: 'Columns', value: 'columns' }
];

function TablePageHeader(props) {
  const { table, handleDeleteObjectModalOpen, isAdmin } = props;
  const [openFeed, setOpenFeed] = useState(false);
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Table {table.name}
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link
            underline="hover"
            component={RouterLink}
            color="textPrimary"
            variant="subtitle2"
            to="/console/catalog"
          >
            Discover
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/datasets"
            variant="subtitle2"
          >
            Datasets
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/redshift-datasets/${table?.dataset?.datasetUri}`}
            variant="subtitle2"
          >
            {table?.dataset?.name}
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/redshift-datasets/table/${table.tableUri}`}
            variant="subtitle2"
          >
            {table.name}
          </Link>
        </Breadcrumbs>
      </Grid>
      {isAdmin && (
        <Grid item>
          <Box sx={{ m: -1 }}>
            <Button
              color="primary"
              startIcon={<ForumOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={() => setOpenFeed(true)}
              type="button"
              variant="outlined"
            >
              Chat
            </Button>
            <Button
              color="primary"
              component={RouterLink}
              startIcon={<PencilAltIcon fontSize="small" />}
              sx={{ m: 1 }}
              to={`/console/redshift-datasets/table/${table.rsTableUri}/edit`}
              variant="outlined"
            >
              Edit
            </Button>
            <Button
              color="primary"
              startIcon={<FaTrash size={15} />}
              sx={{ m: 1 }}
              onClick={handleDeleteObjectModalOpen}
              type="button"
              variant="outlined"
            >
              Delete
            </Button>
          </Box>
        </Grid>
      )}
      {openFeed && (
        <FeedComments
          objectOwner={table.dataset.owner}
          targetType="RedshiftDatasetTable"
          targetUri={table.rsTableUri}
          open={openFeed}
          onClose={() => setOpenFeed(false)}
        />
      )}
    </Grid>
  );
}

TablePageHeader.propTypes = {
  table: PropTypes.object.isRequired,
  handleDeleteObjectModalOpen: PropTypes.func.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

const RSTableView = () => {
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [table, setTable] = useState({});
  const [currentTab, setCurrentTab] = useState(tabs[0].value);
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const deleteTable = async () => {
    const response = await client.mutate(
      deleteRedshiftDatasetTable({
        rsTableUri: table.rsTableUri
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Table deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate(`/console/redshift-datasets/${table.datasetUri}`);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getRedshiftDatasetTable({ rsTableUri: params.uri })
    );
    if (!response.errors && response.data.getRedshiftDatasetTable !== null) {
      setTable(response.data.getRedshiftDatasetTable);
      setIsAdmin(
        ['Creator', 'Admin', 'Owner'].indexOf(
          response.data.getRedshiftDatasetTable.dataset.userRoleForDataset
        ) !== -1
      );
    } else {
      setTable(null);
      const error = response.errors
        ? response.errors[0].message
        : 'Redshift Dataset table not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  if (loading) {
    return <CircularProgress />;
  }

  if (!table) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Tables: Table Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <TablePageHeader
            table={table}
            handleDeleteObjectModalOpen={handleDeleteObjectModalOpen}
            isAdmin={isAdmin}
          />
          <Box sx={{ mt: 3 }}>
            <Tabs
              indicatorColor="primary"
              onChange={handleTabsChange}
              scrollButtons="auto"
              textColor="primary"
              value={currentTab}
              variant="fullWidth"
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  icon={settings.tabIcons ? tab.icon : null}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'overview' && (
              <TableOverview table={table} isAdmin={isAdmin} />
            )}
            {currentTab === 'columns' && <TableColumns table={table} />}
          </Box>
        </Container>
      </Box>
      {isAdmin && (
        <DeleteObjectModal
          objectName={table.label}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={deleteTable}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Redshift Table will be deleted from data.all
                  catalog, but will still be available in Amazon Redshift.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
    </>
  );
};

export default RSTableView;
