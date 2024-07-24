import {
  Box,
  Card,
  Divider,
  Grid,
  Link,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import * as FaIcons from 'react-icons/fa';
import * as FiIcons from 'react-icons/fi';
import { useNavigate } from 'react-router';
import { IconAvatar, useCardStyle } from 'design';

export const MetadataFormListItem = (props) => {
  const { metadata_form } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={metadata_form.uri} md={3} xs={12} {...props}>
      <Card key={metadata_form.uri} className={classes.card} raised>
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
                      navigate(`/console/s3-datasets/${metadata_form.uri}`);
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
                    <Tooltip title={metadata_form.name}>
                      <span>{metadata_form.name}</span>
                    </Tooltip>
                  </Link>
                  <Typography color="textSecondary" variant="body2">
                    by{' '}
                    <Link
                      underline="hover"
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {metadata_form.owner}
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
            <Tooltip
              title={metadata_form.description || 'No description provided'}
            >
              <span>
                {metadata_form.description || 'No description provided'}
              </span>
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
                <Tooltip title={metadata_form.SamlGroupName || '-'}>
                  <span>{metadata_form.SamlGroupName || '-'}</span>
                </Tooltip>
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
            key={metadata_form.visibility}
            justifyContent="space-between"
            spacing={3}
          />
        </Box>
        <Divider />
      </Card>
    </Grid>
  );
};
MetadataFormListItem.propTypes = {
  metadata_form: PropTypes.object.isRequired
};
