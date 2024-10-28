import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { Label, UserModal } from 'design';
import { isFeatureEnabled } from 'utils';
import { useState } from 'react';

export const DatasetGovernance = (props) => {
  const { dataset } = props;
  const terms =
    dataset.terms.nodes.length > 0
      ? dataset.terms.nodes
      : [{ label: '-', nodeUri: '-' }];
  const tags = dataset.tags.length > 0 ? dataset.tags : ['-'];

  const [modalOpen, setIsModalOpen] = useState(false);
  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  const [stewardsModalOpen, setStewardsModalOpen] = useState(false);
  const handleOpenStewardsModal = () => setStewardsModalOpen(true);
  const handleCloseStewardsModal = () => setStewardsModalOpen(false);

  return (
    <Grid container spacing={2}>
      <Grid item lg={6} xl={6} xs={12}>
        <Card {...dataset} sx={{ width: 1, height: '100%' }}>
          <CardHeader title="Classification" />
          <Divider />
          {isFeatureEnabled('datasets_base', 'confidentiality_dropdown') && (
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">
                Confidentiality
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Label color="primary">{dataset.confidentiality}</Label>
              </Box>
            </CardContent>
          )}
          {isFeatureEnabled('datasets_base', 'topics_dropdown') && (
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">
                Topics
              </Typography>
              <Box sx={{ mt: 1 }}>
                {dataset.topics &&
                  dataset.topics.length > 0 &&
                  dataset.topics.map((t) => (
                    <Chip
                      sx={{ mr: 0.5, mb: 0.5 }}
                      key={t}
                      label={t}
                      variant="outlined"
                    />
                  ))}
              </Box>
            </CardContent>
          )}

          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Tags
            </Typography>
            <Box sx={{ mt: 1 }}>
              {tags &&
                tags.map((t) => (
                  <Chip
                    sx={{ mr: 0.5, mb: 0.5 }}
                    key={t}
                    label={t}
                    variant="outlined"
                  />
                ))}
            </Box>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Glossary terms
            </Typography>
            <Box sx={{ mt: 1 }}>
              {terms &&
                terms.map((term) => (
                  <Chip
                    key={term.nodeUri}
                    label={term.label}
                    variant="outlined"
                  />
                ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item lg={6} xl={6} xs={12}>
        <Card {...dataset} sx={{ width: 1, height: '100%' }}>
          <CardHeader title="Governance" />
          <Divider />
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Owners
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <div onClick={handleOpenModal} style={{ cursor: 'pointer' }}>
                {dataset.SamlAdminGroupName}
              </div>
              <UserModal
                team={dataset.SamlAdminGroupName}
                open={modalOpen}
                onClose={handleCloseModal}
              />
            </Typography>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Stewards
            </Typography>
            <Typography color="textPrimary" variant="body2">
              <div
                onClick={handleOpenStewardsModal}
                style={{ cursor: 'pointer' }}
              >
                {dataset.stewards}
              </div>
              <UserModal
                team={dataset.stewards}
                open={stewardsModalOpen}
                onClose={handleCloseStewardsModal}
              />
            </Typography>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Auto-Approval
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Label color="primary">
                {dataset.autoApprovalEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Box>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Expiration Setting for Shares
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Label color="primary">
                {dataset.expirySetting ? dataset.expirySetting : 'Disabled'}
              </Label>
            </Box>
          </CardContent>
          {dataset.enableExpiration === true && (
            <>
              <CardContent>
                <Typography color="textSecondary" variant="subtitle2">
                  Expiration duration ( Minimum ) in{' '}
                  {/*Check how can this hard coding be changed*/}
                  {dataset.expirySetting === 'Quarterly'
                    ? 'Quarters'
                    : 'Months'}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography color="textPrimary" variant="body2">
                    {dataset.expiryMinDuration}
                  </Typography>
                </Box>
              </CardContent>
              <CardContent>
                <Typography color="textSecondary" variant="subtitle2">
                  Expiration duration ( Maximum ) in{' '}
                  {/*Check how can this hard coding be changes*/}
                  {dataset.expirySetting === 'Quarterly'
                    ? 'Quarters'
                    : 'Months'}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography color="textPrimary" variant="body2">
                    {dataset.expiryMaxDuration}
                  </Typography>
                </Box>
              </CardContent>
            </>
          )}
        </Card>
      </Grid>
    </Grid>
  );
};

DatasetGovernance.propTypes = {
  dataset: PropTypes.object.isRequired
};
