import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
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
} from '@material-ui/core';
import * as PropTypes from 'prop-types';
import { FaTrash } from 'react-icons/all';
import { useNavigate } from 'react-router';
import { ForumOutlined, Warning } from '@material-ui/icons';
import useSettings from '../../hooks/useSettings';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getDatasetTable from '../../api/DatasetTable/getDatasetTable';
import deleteDatasetTable from '../../api/DatasetTable/deleteDatasetTable';
import TablePreview from './TablePreview';
import TableMetrics from './TableMetrics';
import TableColumns from './TableColumns';
import TableOverview from './TableOverview';
import PencilAltIcon from '../../icons/PencilAlt';
import DeleteObjectModal from '../../components/DeleteObjectModal';
import FeedComments from '../Feed/FeedComments';

const tabs = [
  { label: 'Preview', value: 'preview' },
  { label: 'Overview', value: 'overview' },
  { label: 'Columns', value: 'columns' },
  { label: 'Metrics', value: 'metrics' }
];

function TablePageHeader(props) {
  const { table, handleDeleteObjectModalOpen, isAdmin } = props;
  const [openFeed, setOpenFeed] = useState(false);
  return (
    <Grid
      container
      justifyContent="space-between"
      spacing={3}
    >
      <Grid item>
        <Typography
          color="textPrimary"
          variant="h5"
        >
          Table
          {' '}
          {table.GlueTableName}
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link
            component={RouterLink}
            color="textPrimary"
            variant="subtitle2"
            to="/console/catalog"
          >
            Discover
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to="/console/datasets"
            variant="subtitle2"
          >
            Datasets
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to={`/console/datasets/${table?.dataset?.datasetUri}`}
            variant="subtitle2"
          >
            {table?.dataset?.name}
          </Link>
          <Link
            color="textPrimary"
            component={RouterLink}
            to={`/console/datasets/table/${table.tableUri}`}
            variant="subtitle2"
          >
            {table.GlueTableName}
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
            to={`/console/datasets/table/${table.tableUri}/edit`}
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
  const [currentTab, setCurrentTab] = useState('preview');
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
    const response = await client.mutate(deleteDatasetTable({ tableUri: table.tableUri }));
    if (!response.errors) {
      navigate(`/console/datasets/${table.datasetUri}`);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fetchItem = async () => {
    setLoading(true);
    const response = await client.query(getDatasetTable(params.uri));
    if (!response.errors && response.data.getDatasetTable !== null) {
      setTable(response.data.getDatasetTable);
      setIsAdmin(['Creator', 'Admin', 'Owner'].indexOf(response.data.getDatasetTable.dataset.userRoleForDataset) !== -1);
    } else {
      setTable(null);
      const error = response.errors ? response.errors[0].message : 'Dataset table not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };
  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

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
              variant="scrollable"
            >
              {tabs.map((tab) => (
                <Tab
                  key={tab.value}
                  label={tab.label}
                  value={tab.value}
                  icon={settings.tabIcons ? tab.icon : null}
                />
              ))}
            </Tabs>
          </Box>
          <Divider />
          <Box sx={{ mt: 3 }}>
            {currentTab === 'preview'
            && <TablePreview table={table} />}
            {currentTab === 'overview'
                        && (
                        <TableOverview
                          table={table}
                          isAdmin={isAdmin}
                        />
                        )}
            {currentTab === 'columns'
                        && (
                        <TableColumns
                          table={table}
                          isAdmin={isAdmin}
                        />
                        )}
            {currentTab === 'metrics'
                        && (
                        <TableMetrics
                          table={table}
                          isAdmin={isAdmin}
                        />
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
        deleteMessage={(
          <Card>
            <CardContent>
              <Typography
                gutterBottom
                variant="body2"
              >
                <Warning />
                {' '}
                Table will be deleted from data.all catalog, but will still be available on AWS Glue catalog.
              </Typography>
            </CardContent>
          </Card>
        )}
      />
      )}
    </>
  );
};

export default TableView;
