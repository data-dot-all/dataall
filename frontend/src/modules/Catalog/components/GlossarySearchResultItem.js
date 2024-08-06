import { LockOpen, ThumbUp } from '@mui/icons-material';
import {
  Box,
  Card,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Button,
  Link,
  Tooltip,
  Typography,
  Avatar
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useState } from 'react';
import * as FaIcons from 'react-icons/fa';
import { Link as RouterLink } from 'react-router-dom';
import { useCardStyle } from 'design';
import { dayjs } from 'utils';
import { RequestAccessModal } from './RequestAccessModal';
import { RequestDashboardAccessModal } from './RequestDashboardAccessModal';
import { RequestRedshiftAccessModal } from './RequestRedshiftAccessModal';

// Add new types of items by adding them in the following type_dicts
// DO NOT change the returned frontend view

const icon_paths_by_type = {
  dataset: '/static/icons/Arch_Amazon-Simple-Storage-Service_64.svg',
  table: '/static/icons/Arch_Amazon-Simple-Storage-Service_64.svg',
  folder: '/static/icons/Arch_Amazon-Simple-Storage-Service_64.svg',
  dashboard: '/static/icons/Arch_Amazon-Quicksight_64.svg',
  redshiftdataset: '/static/icons/Arch_Amazon-Redshift_64.svg',
  redshifttable: '/static/icons/Arch_Amazon-Redshift_64.svg'
};

const redirect_link_by_type = {
  dataset: '/console/s3-datasets/',
  table: '/console/s3-datasets/table/',
  folder: '/console/s3-datasets/folder/',
  dashboard: '/console/dashboards/',
  redshiftdataset: '/console/redshift-datasets/',
  redshifttable: '/console/redshift-datasets/table/'
};

const tooltip_message_by_type = {
  dataset: `Create the request in which to add Glue tables, S3 prefixes and S3 Buckets`,
  table: `Create the request to a S3/Glue Dataset already adding this table`,
  folder: `Create the request to a S3/Glue Dataset already adding this folder`,
  dashboard: `Create the request to a Quicksight Dashboard`,
  redshiftdataset: `Create the request in which to add Redshift tables`,
  redshifttable: `Create the request to a Redshift Dataset already adding this table`
};

const tooltip_span_by_type = {
  dataset: `S3/Glue Dataset`,
  table: `Glue Table`,
  folder: `S3 Prefix`,
  dashboard: `Quicksight Dashboard`,
  redshiftdataset: `Redshift Dataset`,
  redshifttable: `Redshift Table`
};

const upvotes_enabled_by_type = {
  dataset: true,
  table: false,
  folder: false,
  dashboard: false,
  redshiftdataset: true,
  redshifttable: false
};

export const GlossarySearchResultItem = ({ hit }) => {
  const classes = useCardStyle();
  const [isRequestAccessOpen, setIsRequestAccessOpen] = useState(false);
  const [isOpeningModal, setIsOpeningModal] = useState(false);
  const [isRequestDashboardAccessOpen, setIsRequestDashboardAccessOpen] =
    useState(false);
  const [isOpeningDashboardModal, setIsOpeningDashboardModal] = useState(false);
  const [isRequestRedshiftAccessOpen, setIsRequestRedshiftAccessOpen] =
    useState(false);
  const [isOpeningRedshiftModal, setIsOpeningRedshiftModal] = useState(false);
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

  const handleRequestRedshiftAccessModalOpen = () => {
    setIsOpeningRedshiftModal(true);
    setIsRequestRedshiftAccessOpen(true);
  };

  const handleRequestRedshiftAccessModalClose = () => {
    setIsOpeningRedshiftModal(false);
    setIsRequestRedshiftAccessOpen(false);
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
          <Avatar
            src={icon_paths_by_type[hit.resourceKind]}
            size={25}
            variant="square"
          />
          <Box sx={{ ml: 2 }}>
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
            to={`${redirect_link_by_type[hit.resourceKind]}${hit._id}/`} /*eslint-disable-line*/
              variant="h6"
            >
              {hit.label}
            </Link>

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
              <Tooltip title={tooltip_message_by_type[hit.resourceKind]}>
                <span>{tooltip_span_by_type[hit.resourceKind]}</span>
              </Tooltip>
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
        <Typography color="textSecondary" variant="body2">
          by{' '}
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            {hit.owner}
          </Link>{' '}
          | created {dayjs(hit.created).fromNow()}
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
      <Box
        sx={{
          pb: 2,
          px: 3
        }}
      >
        {hit.tags && hit.tags.length > 0 && (
          <Box>
            {hit.topics.concat(hit.tags.slice(0, 5)).map((tag) => (
              <Chip
                sx={{ mr: 0.5, mb: 0.5 }}
                key={tag}
                label={
                  <Typography color="textPrimary" variant="subtitle2">
                    {tag}
                  </Typography>
                }
                variant="filled"
              />
            ))}
          </Box>
        )}
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
          {isOpeningModal ||
          isOpeningDashboardModal ||
          isOpeningRedshiftModal ? (
            <CircularProgress size={20} />
          ) : (
            <Button
              color="primary"
              startIcon={<LockOpen fontSize="small" />}
              onClick={() =>
                hit.resourceKind === 'dashboard'
                  ? handleRequestDashboardAccessModalOpen()
                  : hit.resourceKind === 'dataset' ||
                    hit.resourceKind === 'table' ||
                    hit.resourceKind === 'folder'
                  ? handleRequestAccessModalOpen()
                  : hit.resourceKind === 'redshiftdataset' ||
                    hit.resourceKind === 'redshifttable'
                  ? handleRequestRedshiftAccessModalOpen()
                  : '-'
              }
              type="button"
            >
              Request Access
            </Button>
          )}
          <RequestAccessModal
            hit={hit}
            onApply={handleRequestAccessModalClose}
            open={isRequestAccessOpen}
            stopLoader={() => setIsOpeningModal(false)}
          />
          <RequestRedshiftAccessModal
            hit={hit}
            onApply={handleRequestRedshiftAccessModalClose}
            open={isRequestRedshiftAccessOpen}
            stopLoader={() => setIsOpeningRedshiftModal(false)}
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
        {upvotes_enabled_by_type[hit.resourceKind] &&
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
GlossarySearchResultItem.propTypes = {
  hit: PropTypes.object.isRequired
};
