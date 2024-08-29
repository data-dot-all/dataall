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
import * as FaIcons from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { IconAvatar, Label, useCardStyle } from 'design';
import { BallotOutlined } from '@mui/icons-material';
import React from 'react';

export const MetadataFormListItem = (props) => {
  const { metadata_form, visibilityDict } = props;
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
                <IconAvatar icon={<BallotOutlined size={18} />} />
                <Box
                  sx={{
                    ml: 2,
                    whiteSpace: 'nowrap',
                    alignItems: 'left'
                  }}
                >
                  <Link
                    underline="hover"
                    component="button"
                    color="textPrimary"
                    variant="h6"
                    onClick={() => {
                      navigate(`/console/metadata-forms/${metadata_form.uri}`);
                    }}
                    sx={{
                      maxWidth: '200px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    <Tooltip title={metadata_form.name}>
                      <span>{metadata_form.name}</span>
                    </Tooltip>
                  </Link>
                  <Typography color="textSecondary" variant="body2">
                    owned by{' '}
                    <Link
                      color="textPrimary"
                      variant="subtitle2"
                      underline="false"
                    >
                      {metadata_form.SamlGroupName}
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
            py: 1
          }}
        >
          <Grid container>
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaUserShield /> My Role
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              {metadata_form.userRole === 'Owner' ? (
                <Label color="primary">{metadata_form.userRole || '-'}</Label>
              ) : (
                <Typography color="textSecondary" variant="body2">
                  {metadata_form.userRole || '-'}
                </Typography>
              )}
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid container>
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaEye /> Visibility
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
                <Tooltip title={metadata_form.visibility || '-'}>
                  <span>{metadata_form.visibility || '-'}</span>
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
          <Grid container sx={{ minHeight: '25px' }}>
            <Grid item md={4} xs={12}>
              {metadata_form.visibility !== visibilityDict.Global && (
                <Typography color="textSecondary" variant="body2">
                  <FaIcons.FaUsersCog />{' '}
                  {Object.keys(visibilityDict).find(
                    (key) => visibilityDict[key] === metadata_form.visibility
                  )}
                </Typography>
              )}
            </Grid>
            <Grid item md={8} xs={12}>
              {metadata_form.visibility !== visibilityDict.Global && (
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
                  <Tooltip title={metadata_form.homeEntity || '-'}>
                    <Link
                      color="textPrimary"
                      variant="subtitle2"
                      underline="false"
                      sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}
                    >
                      {metadata_form.homeEntityName || '-'}
                    </Link>
                  </Tooltip>
                </Typography>
              )}
            </Grid>
          </Grid>
        </Box>

        <Divider />
      </Card>
    </Grid>
  );
};
MetadataFormListItem.propTypes = {
  metadata_form: PropTypes.object.isRequired,
  visibilityDict: PropTypes.object.isRequired
};
