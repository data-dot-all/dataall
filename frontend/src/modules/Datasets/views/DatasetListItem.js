import {
  Box,
  Button,
  Card,
  Divider,
  Grid,
  Link,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import * as BsIcons from 'react-icons/bs';
import { BsTable } from 'react-icons/bs';
import * as FaIcons from 'react-icons/fa';
import * as FiIcons from 'react-icons/fi';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import {
  IconAvatar,
  Label,
  StackStatus,
  UpVotesReadOnly,
  useCardStyle
} from '../../../../design';

const DatasetListItem = (props) => {
  const { dataset } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={dataset.datasetUri} md={3} xs={12} {...props}>
      <Card key={dataset.datasetUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Grid container>
            <Grid item md={11} xs={11}>
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex'
                }}
              >
                <IconAvatar icon={<FiIcons.FiPackage size={18} />} />
                <Box sx={{ ml: 2 }}>
                  <Link
                    underline="hover"
                    component="button"
                    color="textPrimary"
                    variant="h6"
                    onClick={() => {
                      navigate(`/console/datasets/${dataset.datasetUri}`);
                    }}
                    sx={{
                      width: '99%',
                      whiteSpace: 'nowrap',
                      alignItems: 'left',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      WebkitBoxOrient: 'vertical',
                      WebkitLineClamp: 2
                    }}
                  >
                    <Tooltip title={dataset.label}>
                      <span>{dataset.label}</span>
                    </Tooltip>
                  </Link>
                  <Typography color="textSecondary" variant="body2">
                    by{' '}
                    <Link
                      underline="hover"
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {dataset.owner}
                    </Link>
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
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
              width: '200px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              WebkitBoxOrient: 'vertical',
              WebkitLineClamp: 2
            }}
          >
            <Tooltip title={dataset.description || 'No description provided'}>
              <span>{dataset.description || 'No description provided'}</span>
            </Tooltip>
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
                <FaIcons.FaUserShield /> Role
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Label
                color={
                  dataset.userRoleForDataset === 'Creator' ? 'primary' : 'info'
                }
              >
                {dataset.userRoleForDataset || '-'}
              </Label>
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
                <FaIcons.FaUsersCog /> Team
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Typography
                color="textPrimary"
                variant="body2"
                sx={{
                  width: '200px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2
                }}
              >
                <Tooltip title={dataset.SamlAdminGroupName || '-'}>
                  <span>{dataset.SamlAdminGroupName || '-'}</span>
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
                <BsTable /> Tables
              </Typography>
            </Grid>
            <Grid item md={8} xs={6}>
              <Typography color="textPrimary" variant="body2">
                {dataset.statistics.tables}
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
                <BsIcons.BsFolder /> Folders
              </Typography>
            </Grid>
            <Grid item md={8} xs={6}>
              <Typography color="textPrimary" variant="body2">
                {dataset.statistics.locations}
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
                <FiIcons.FiActivity /> Status
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Typography color="textPrimary" variant="body2">
                <StackStatus
                  status={dataset.stack ? dataset.stack.status : 'NOT_FOUND'}
                />
              </Typography>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid
            alignItems="center"
            container
            key={dataset.environmentUri}
            justifyContent="space-between"
            spacing={3}
          />
        </Box>
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            pl: 1,
            pr: 3,
            py: 0.5
          }}
        >
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <Button
              color="primary"
              component={RouterLink}
              to={`/console/datasets/${dataset.datasetUri}`}
            >
              Learn More
            </Button>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          <UpVotesReadOnly upvotes={dataset.statistics.upvotes} />
        </Box>
      </Card>
    </Grid>
  );
};
DatasetListItem.propTypes = {
  dataset: PropTypes.object.isRequired
};
export default DatasetListItem;
