import {
  Avatar,
  Box,
  Button,
  Card,
  Grid,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';
import { ShareStatus, useCardStyle } from 'design';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { UserModal } from 'design';
import React, { useState } from 'react';

export const ShareBoxListItem = ({ share }) => {
  const classes = useCardStyle();
  const dataset_icon =
    share.dataset.datasetType === 'DatasetTypes.S3'
      ? '/static/icons/Arch_Amazon-Simple-Storage-Service_64.svg'
      : share.dataset.datasetType === 'DatasetTypes.Redshift'
      ? '/static/icons/Arch_Amazon-Redshift_64.svg'
      : '-';

  const [ModalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  const [DataOwnerModalOpen, setIsDataOwnerModalOpen] = useState(false);
  const handleDataOwnerOpenModal = () => {
    setIsDataOwnerModalOpen(true);
  };
  const handleCloseDataOwnerModal = () => {
    setIsDataOwnerModalOpen(false);
  };

  return (
    <Card
      key={share.shareUri}
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container spacing={0.5} alignItems="center">
        <Grid item justifyContent="center" md={0.5} lg={0.5} xl={0.5}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Avatar src={`${dataset_icon}`} size={15} variant="square" />
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2.2} lg={1.5} xl={1.2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <ShareStatus status={share.status} />
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Request owner
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              <div sx={{ cursor: 'pointer' }} onClick={handleOpenModal}>
                {`${share.principal.SamlGroupName}`}
              </div>
              <UserModal
                teams={share.principal.SamlGroupName}
                open={ModalOpen}
                onClose={handleCloseModal}
              />
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Role name
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${share.principal.principalRoleName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Dataset
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${share.dataset.datasetName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography
              color="textPrimary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              Dataset Owner
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ cursor: 'pointer', wordWrap: 'break-word' }}
            >
              {/* YAHOO ONLY CHANGE */}
              <div
                sx={{ cursor: 'pointer' }}
                onClick={handleDataOwnerOpenModal}
              >
                {`${share.dataset.SamlAdminGroupName}`}
              </div>
            </Typography>
            <UserModal
              teams={share.dataset.SamlAdminGroupName}
              open={DataOwnerModalOpen}
              onClose={handleCloseDataOwnerModal}
            />
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={0.7} lg={0.7} xl={0.7}>
          <Button
            color="primary"
            type="button"
            component={RouterLink}
            to={`/console/shares/${share.shareUri}`}
            variant="contained"
          >
            Open
          </Button>
        </Grid>
        <Grid item justifyContent="flex-end" md={0.2} lg={0.2} xl={0.4}>
          {share.statistics.sharedItems > 0 && (
            <Tooltip
              title={share.statistics.sharedItems + ' shared items'}
              placement="right"
            >
              <CheckCircleIcon color={'success'} />
            </Tooltip>
          )}
          {share.statistics.failedItems > 0 && (
            <Tooltip
              title={share.statistics.failedItems + ' failed items'}
              placement="right"
            >
              <ErrorIcon color={'error'} />
            </Tooltip>
          )}
        </Grid>
      </Grid>
    </Card>
  );
};
ShareBoxListItem.propTypes = {
  share: PropTypes.object.isRequired
};
