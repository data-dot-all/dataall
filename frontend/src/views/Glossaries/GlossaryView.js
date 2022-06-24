import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Box,
  Breadcrumbs,
  Button,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Link,
  Tab,
  Tabs,
  Typography
} from '@mui/material';
import { FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import * as PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import { Info } from '@mui/icons-material';
import useSettings from '../../hooks/useSettings';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import DeleteObjectWithFrictionModal from '../../components/DeleteObjectWithFrictionModal';
import getGlossary from '../../api/Glossary/getGlossary';
import GlossaryAssociations from './GlossaryAssociations';
import GlossaryManagement from './GlossaryManagement';
import useAuth from '../../hooks/useAuth';
import deleteGlossary from '../../api/Glossary/deleteGlossary';

const tabs = [
  { label: 'Overview', value: 'overview', icon: <Info fontSize="small" /> },
  {
    label: 'Associations',
    value: 'associations',
    icon: <Link underline="hover" Icon fontSize="small" />
  }
];

function GlossaryViewPageHeader({ glossary, deleteFunction, isAdmin }) {
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Glossary {glossary.label}
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/glossaries"
            variant="subtitle2"
          >
            Glossaries
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/glossaries/${glossary.nodeUri}`}
            variant="subtitle2"
          >
            {glossary.label}
          </Link>
        </Breadcrumbs>
      </Grid>
      {isAdmin && (
        <Grid item>
          <Box sx={{ m: -1 }}>
            <Button
              color="primary"
              startIcon={<FaTrash size={15} />}
              sx={{ mt: 1 }}
              onClick={deleteFunction}
              type="button"
              variant="outlined"
            >
              Delete
            </Button>
          </Box>
        </Grid>
      )}
    </Grid>
  );
}

GlossaryViewPageHeader.propTypes = {
  glossary: PropTypes.object.isRequired,
  deleteFunction: PropTypes.func.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
const GlossaryView = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const { user } = useAuth();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [glossary, setGlossary] = useState(null);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const handleDeleteObjectModalOpen = () => {
    setIsDeleteObjectModalOpen(true);
  };

  const handleDeleteObjectModalClose = () => {
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getGlossary(params.uri));
    if (!response.errors && response.data.getGlossary !== null) {
      setIsAdmin(
        ['Admin'].indexOf(
          response.data.getGlossary.userRoleForGlossary
        ) !== -1
      );
      setGlossary(response.data.getGlossary);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Glossary not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, user.email]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);
  const handleTabsChange = (event, value) => {
    setCurrentTab(value);
  };

  const deleteGlossaryNode = async () => {
    const response = await client.mutate(deleteGlossary(glossary.nodeUri));
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Glossary deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate('/console/glossaries');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  if (loading) {
    return <CircularProgress />;
  }
  if (!glossary) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Glossaries: Glossaries Details | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <GlossaryViewPageHeader
            glossary={glossary}
            deleteFunction={handleDeleteObjectModalOpen}
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
              <GlossaryManagement
                glossary={glossary}
                client={client}
                isAdmin={isAdmin}
              />
            )}
            {currentTab === 'associations' && (
              <GlossaryAssociations glossary={glossary} />
            )}
          </Box>
        </Container>
      </Box>
      {isDeleteObjectModalOpen && (
        <DeleteObjectWithFrictionModal
          objectName={glossary.label}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={deleteGlossaryNode}
          isAWSResource={false}
        />
      )}
    </>
  );
};

export default GlossaryView;
