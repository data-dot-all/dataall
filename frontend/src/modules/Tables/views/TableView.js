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
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import * as PropTypes from 'prop-types';
import { useLocation, Link as RouterLink, useParams } from 'react-router-dom';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import {
  ChevronRightIcon,
  DeleteObjectModal,
  PencilAltIcon,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { deleteDatasetTable, useClient } from 'services';
import { FeedComments } from 'modules/Shared';
import { getDatasetTable } from '../services';
import {
  TableColumns,
  TableMetrics,
  TableOverview,
  TablePreview,
  TableFilters
} from '../components';
import { isFeatureEnabled } from 'utils';
import config from '../../../generated/config.json';

const previewDataEnabled = isFeatureEnabled('s3_datasets', 'preview_data');
const metricsEnabled = isFeatureEnabled('s3_datasets', 'metrics_data');

const confidentialityOptionsDict =
  config.modules.datasets_base.features.confidentiality_dropdown === true &&
  config.modules.s3_datasets.features.custom_confidentiality_mapping
    ? config.modules.s3_datasets.features.custom_confidentiality_mapping
    : {};

const tabs = [{ label: 'Overview', value: 'overview' }];

function TablePageHeader(props) {
  const { table, handleDeleteObjectModalOpen, isAdmin } = props;
  const [openFeed, setOpenFeed] = useState(false);
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Table {table.label}
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
            to={`/console/s3-datasets/${table?.dataset?.datasetUri}`}
            variant="subtitle2"
          >
            {table?.dataset?.name}
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/s3-datasets/table/${table.tableUri}`}
            variant="subtitle2"
          >
            {table.label}
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
              to={`/console/s3-datasets/table/${table.tableUri}/edit`}
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
          targetType="DatasetTable"
          targetUri={table.tableUri}
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
const TableView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [table, setTable] = useState({});
  const [loading, setLoading] = useState(true);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const location = useLocation();
  const shareUri = location?.state?.shareUri;
  const tab = location?.state?.tab;

  const [currentTab, setCurrentTab] = useState(tab || tabs[0].value);

  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const handleUserRole = useCallback(async (userRole, confidentiality) => {
    const isUnclassified =
      confidentiality === 'Unclassified' ||
      confidentialityOptionsDict[confidentiality] === 'Unclassified';
    const adminValue = ['Creator', 'Admin', 'Owner'].indexOf(userRole) !== -1;
    const stewardValue = ['DataSteward'].indexOf(userRole) !== -1;
    setIsAdmin(adminValue);
    if (adminValue || stewardValue || isUnclassified) {
      if (previewDataEnabled && !tabs.find((t) => t.value === 'preview')) {
        tabs.unshift({ label: 'Preview', value: 'preview' });
      }
      if (!tabs.find((t) => t.value === 'columns')) {
        tabs.push({ label: 'Columns', value: 'columns' });
      }
      if (metricsEnabled && !tabs.find((t) => t.value === 'metrics')) {
        tabs.push({ label: 'Metrics', value: 'metrics' });
      }
      if (
        (adminValue || stewardValue) &&
        !tabs.find((t) => t.value === 'datafilters')
      ) {
        tabs.push({ label: 'Data Filters', value: 'datafilters' });
      }
    }
  }, []);

  const deleteTable = async () => {
    const response = await client.mutate(
      deleteDatasetTable({ tableUri: table.tableUri })
    );
    if (!response.errors) {
      navigate(`/console/s3-datasets/${table.datasetUri}`);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getDatasetTable(params.uri));
    if (response.data.getDatasetTable !== null) {
      setTable(response.data.getDatasetTable);
      handleUserRole(
        response.data.getDatasetTable.dataset.userRoleForDataset,
        response.data.getDatasetTable.dataset.confidentiality
      );
    } else {
      setTable(null);
      const error = response.errors
        ? response.errors[0].message
        : 'Dataset table not found';
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
          {shareUri && (
            <Button
              startIcon={<ArrowBackIcon fontSize="small" />}
              onClick={() => navigate(`/console/shares/${shareUri}`)}
            >
              Go Back to Share Object
            </Button>
          )}
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
            {previewDataEnabled && currentTab === 'preview' && (
              <TablePreview table={table} />
            )}
            {currentTab === 'overview' && (
              <TableOverview table={table} isAdmin={isAdmin} />
            )}
            {currentTab === 'columns' && (
              <TableColumns table={table} isAdmin={isAdmin} />
            )}
            {metricsEnabled && currentTab === 'metrics' && (
              <TableMetrics table={table} isAdmin={isAdmin} />
            )}
            {currentTab === 'datafilters' && isAdmin && (
              <TableFilters table={table} isAdmin={isAdmin} />
            )}
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
                  <Warning /> Table will be deleted from data.all catalog, but
                  will still be available on AWS Glue catalog.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
    </>
  );
};

export default TableView;
