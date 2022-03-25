import { Link as RouterLink } from 'react-router-dom';
import * as BsIcons from 'react-icons/bs';
import * as FiIcons from 'react-icons/fi';
import * as ReactIf from 'react-if';
import {
  Box,
  Card,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Link,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import * as FaIcons from 'react-icons/fa';
import { LockOpen, ThumbUp } from '@mui/icons-material';
import React, { useState } from 'react';
import { MdShowChart } from 'react-icons/md';
import IconAvatar from '../../components/IconAvatar';
import RequestAccessModal from './RequestAccessModal';
import { dayjs } from '../../utils/dayjs';
import RequestDashboardAccessModal from './RequestDashboardAccessModal';
import useCardStyle from '../../hooks/useCardStyle';

const HitICon = ({ hit }) => (
  <ReactIf.Switch>
    <ReactIf.Case condition={hit.resourceKind === 'dataset'}>
      <IconAvatar icon={<FiIcons.FiPackage size={18} />} />
    </ReactIf.Case>
    <ReactIf.Case condition={hit.resourceKind === 'table'}>
      <IconAvatar icon={<BsIcons.BsTable size={18} />} />
    </ReactIf.Case>
    <ReactIf.Case condition={hit.resourceKind === 'folder'}>
      <IconAvatar icon={<BsIcons.BsFolder size={18} />} />
    </ReactIf.Case>
    <ReactIf.Case condition={hit.resourceKind === 'dashboard'}>
      <IconAvatar icon={<MdShowChart size={18} />} />
    </ReactIf.Case>
  </ReactIf.Switch>
);

HitICon.propTypes = {
  hit: PropTypes.object.isRequired
};

const Hit = ({ hit }) => {
  const classes = useCardStyle();
  const [isRequestAccessOpen, setIsRequestAccessOpen] = useState(false);
  const [isOpeningModal, setIsOpeningModal] = useState(false);
  const [isRequestDashboardAccessOpen, setIsRequestDashboardAccessOpen] =
    useState(false);
  const [isOpeningDashboardModal, setIsOpeningDashboardModal] = useState(false);
  const handleRequestAccessModalOpen = () => {
    setIsOpeningModal(true);
    setIsRequestAccessOpen(true);
  };

  const handleRequestAccessModalClose = () => {
    setIsRequestAccessOpen(false);
  };

  const handleRequestDashboardAccessModalOpen = () => {
    setIsOpeningDashboardModal(true);
    setIsRequestDashboardAccessOpen(true);
  };

  const handleRequestDashboardAccessModalClose = () => {
    setIsOpeningDashboardModal(false);
    setIsRequestDashboardAccessOpen(false);
  };

  return (
    <Card sx={{ mb: 2 }} className={classes.card}>
      <Box sx={{ p: 2 }}>
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex'
          }}
        >
          <HitICon hit={hit} />
          <Box sx={{ ml: 2 }}>
            {hit.resourceKind === 'dataset' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/datasets/${hit._id}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
            {hit.resourceKind === 'table' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/datasets/table/${hit._id}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
            {hit.resourceKind === 'folder' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/datasets/folder/${hit._id}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
            {hit.resourceKind === 'dashboard' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/dashboards/${hit._id}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
            <Typography color="textSecondary" variant="body2">
              by{' '}
              <Link underline="hover" color="textPrimary" variant="subtitle2">
                {hit.owner}
              </Link>{' '}
              | created {dayjs(hit.created).fromNow()}
            </Typography>
          </Box>
        </Box>
      </Box>
      <Box
        sx={{
          pb: 2,
          px: 3
        }}
      >
        <Typography
          color="textSecondary"
          variant="body2"
          sx={{
            height: 20,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            WebkitBoxOrient: 'vertical',
            WebkitLineClamp: 2
          }}
        >
          {hit.description || 'No description provided'}
        </Typography>
      </Box>
      <Box
        sx={{
          px: 3,
          py: 0.5
        }}
      >
        <Grid container>
          <Grid item md={4} xs={12}>
            <Typography color="textSecondary" variant="body2">
              <FaIcons.FaUsersCog /> Team
            </Typography>
          </Grid>
          <Grid item md={8} xs={12}>
            <Typography
              color="textPrimary"
              variant="subtitle2"
              sx={{
                width: '200px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                WebkitBoxOrient: 'vertical',
                WebkitLineClamp: 2
              }}
            >
              <Tooltip title={hit.admins || '-'}>
                <span>{hit.admins || '-'}</span>
              </Tooltip>
            </Typography>
          </Grid>
        </Grid>
      </Box>
      <Box
        sx={{
          px: 3,
          py: 0.5
        }}
      >
        <Grid container>
          <Grid item md={4} xs={12}>
            <Typography color="textSecondary" variant="body2">
              <FaIcons.FaCloud />
              {' Environment'}
            </Typography>
          </Grid>
          <Grid item md={8} xs={12}>
            <Typography
              color="textPrimary"
              variant="subtitle2"
              sx={{
                width: '200px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                WebkitBoxOrient: 'vertical',
                WebkitLineClamp: 2,
                ml: 0.25
              }}
            >
              <Tooltip title={hit.environmentName || '-'}>
                <span>{hit.environmentName || '-'}</span>
              </Tooltip>
            </Typography>
          </Grid>
        </Grid>
      </Box>
      <Box
        sx={{
          px: 3,
          py: 0.5,
          mb: 2
        }}
      >
        <Grid container>
          <Grid item md={4} xs={12}>
            <Typography color="textSecondary" variant="body2">
              <FaIcons.FaGlobe /> Region
            </Typography>
          </Grid>
          <Grid item md={8} xs={12}>
            <Typography color="textPrimary" variant="subtitle2">
              {hit.region}
            </Typography>
          </Grid>
        </Grid>
      </Box>
      <Divider />
      <Box
        sx={{
          alignItems: 'center',
          display: 'flex',
          pl: 1,
          pr: 3,
          py: 1
        }}
      >
        <Box>
          {isOpeningModal || isOpeningDashboardModal ? (
            <CircularProgress size={20} />
          ) : (
            <Tooltip title="Request Access">
              <IconButton
                color="primary"
                edge="end"
                onClick={() =>
                  hit.resourceKind === 'dashboard'
                    ? handleRequestDashboardAccessModalOpen()
                    : handleRequestAccessModalOpen()
                }
              >
                <LockOpen fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <RequestAccessModal
            hit={hit}
            onApply={handleRequestAccessModalClose}
            onClose={handleRequestAccessModalClose}
            open={isRequestAccessOpen}
            stopLoader={() => setIsOpeningModal(false)}
          />
          <RequestDashboardAccessModal
            hit={hit}
            onApply={handleRequestDashboardAccessModalClose}
            onClose={handleRequestDashboardAccessModalClose}
            open={isRequestDashboardAccessOpen}
            stopLoader={() => setIsOpeningDashboardModal(false)}
          />
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {(hit.resourceKind === 'dashboard' || hit.resourceKind === 'dataset') &&
          hit.upvotes !== undefined &&
          hit.upvotes >= 0 && (
            <Tooltip title="UpVotes">
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex'
                }}
              >
                <IconButton color="primary" disabled>
                  <ThumbUp fontSize="small" />
                </IconButton>

                <Typography color="textSecondary" variant="subtitle2">
                  {hit.upvotes}
                </Typography>
              </Box>
            </Tooltip>
          )}
      </Box>
    </Card>
  );
};
Hit.propTypes = {
  hit: PropTypes.object.isRequired
};
export default Hit;
