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
import * as ReactIf from 'react-if';
import { Link as RouterLink } from 'react-router-dom';
import { useCardStyle } from 'design';
import { dayjs } from 'utils';
import { RequestAccessModal } from './RequestAccessModal';
import { RequestDashboardAccessModal } from './RequestDashboardAccessModal';

const HitICon = ({ hit }) => (
  <ReactIf.Switch>
    <ReactIf.Case
      condition={
        hit.resourceKind === 'dataset' ||
        hit.resourceKind === 'table' ||
        hit.resourceKind === 'folder'
      }
    >
      <Avatar
        src={`/static/icons/Arch_Amazon-Simple-Storage-Service_64.svg`}
        size={25}
        variant="square"
      />
    </ReactIf.Case>
    <ReactIf.Case
      condition={
        hit.resourceKind === 'redshiftdataset' ||
        hit.resourceKind === 'redshifttable'
      }
    >
      <Avatar
        src={`/static/icons/Arch_Amazon-Redshift_64.svg`}
        size={25}
        variant="square"
      />
    </ReactIf.Case>
    <ReactIf.Case condition={hit.resourceKind === 'dashboard'}>
      <Avatar
        src={`/static/icons/Arch_Amazon-Quicksight_64.svg`}
        size={25}
        variant="square"
      />
    </ReactIf.Case>
  </ReactIf.Switch>
);

HitICon.propTypes = {
  hit: PropTypes.object.isRequired
};

export const GlossarySearchResultItem = ({ hit }) => {
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
                to={`/console/s3-datasets/${hit._id}/`} /*eslint-disable-line*/
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
                to={`/console/s3-datasets/table/${hit._id}/`} /*eslint-disable-line*/
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
                to={`/console/s3-datasets/folder/${hit._id}/`} /*eslint-disable-line*/
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
            {hit.resourceKind === 'redshiftdataset' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/redshift-datasets/${hit._id}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
            {hit.resourceKind === 'redshifttable' && (
              <Link
                underline="hover"
                color="textPrimary"
                component={RouterLink}
                to={`/console/redshift-datasets/${hit.datasetUri}/`} /*eslint-disable-line*/
                variant="h6"
              >
                {hit.label}
              </Link>
            )}
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
              <Tooltip
                title={
                  hit.resourceKind === 'dataset'
                    ? `Create the request in which to add Glue tables, S3 prefixes and S3 Buckets`
                    : hit.resourceKind === 'table'
                    ? `Create the request to a S3/Glue Dataset already adding this table`
                    : hit.resourceKind === 'folder'
                    ? `Create the request to a S3/Glue Dataset already adding this folder`
                    : hit.resourceKind === 'redshiftdataset'
                    ? `Create the request in which to add Redshift tables`
                    : hit.resourceKind === 'redshifttable'
                    ? `Create the request to a Redshift Dataset already adding this table`
                    : '-'
                }
              >
                <span>
                  {hit.resourceKind === 'dataset'
                    ? `S3/Glue Dataset`
                    : hit.resourceKind === 'table'
                    ? `Glue Table `
                    : hit.resourceKind === 'folder'
                    ? `S3 Prefix`
                    : hit.resourceKind === 'redshiftdataset'
                    ? `Redshift Dataset`
                    : hit.resourceKind === 'redshifttable'
                    ? `Redshift Table`
                    : '-'}
                </span>
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
          {isOpeningModal || isOpeningDashboardModal ? (
            <CircularProgress size={20} />
          ) : (
            <Button
              color="primary"
              startIcon={<LockOpen fontSize="small" />}
              onClick={() =>
                hit.resourceKind === 'dashboard'
                  ? handleRequestDashboardAccessModalOpen()
                  : handleRequestAccessModalOpen()
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
          <RequestDashboardAccessModal
            hit={hit}
            onApply={handleRequestDashboardAccessModalClose}
            onClose={handleRequestDashboardAccessModalClose}
            open={isRequestDashboardAccessOpen}
            stopLoader={() => setIsOpeningDashboardModal(false)}
          />
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {(hit.resourceKind === 'dashboard' ||
          hit.resourceKind === 'dataset' ||
          hit.resourceKind === 'redshiftdataset') &&
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
