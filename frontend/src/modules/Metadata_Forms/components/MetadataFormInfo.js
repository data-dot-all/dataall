import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  List,
  ListItem,
  Typography
} from '@mui/material';

export const MetadataFormInfo = (props) => {
  const { metadataForm, visibilityDict } = props;
  return (
    <>
      <Grid container spacing={2}>
        <Grid item lg={3} xl={3} xs={6}>
          <Card sx={{ height: '100%' }}>
            <Box>
              <CardHeader title={'Details'} />
              <Divider />
            </Box>
            <CardContent>
              <List>
                <ListItem
                  disableGutters
                  divider
                  sx={{
                    justifyContent: 'space-between',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxLines: 1
                  }}
                >
                  <Typography color="textSecondary" variant="subtitle2">
                    Name
                  </Typography>
                  <Typography
                    color="textPrimary"
                    variant="subtitle2"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxLines: 1,
                      ml: 5
                    }}
                  >
                    {metadataForm.name}
                  </Typography>
                </ListItem>
                <ListItem
                  disableGutters
                  divider
                  sx={{
                    justifyContent: 'space-between'
                  }}
                >
                  <Typography color="textSecondary" variant="subtitle2">
                    URI
                  </Typography>
                  <Typography color="textPrimary" variant="subtitle2">
                    {metadataForm.uri}
                  </Typography>
                </ListItem>
                <ListItem
                  disableGutters
                  divider
                  sx={{
                    justifyContent: 'space-between'
                  }}
                >
                  <Typography color="textSecondary" variant="subtitle2">
                    Visibility
                  </Typography>
                  <Typography color="textPrimary" variant="subtitle2">
                    {metadataForm.visibility}
                  </Typography>
                </ListItem>
                <ListItem
                  disableGutters
                  divider
                  sx={{
                    justifyContent: 'space-between'
                  }}
                >
                  <Typography color="textSecondary" variant="subtitle2">
                    {Object.keys(visibilityDict).find(
                      (key) => visibilityDict[key] === metadataForm.visibility
                    )}
                  </Typography>
                  <Typography
                    color="textPrimary"
                    variant="subtitle2"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxLines: 1,
                      ml: 5
                    }}
                  >
                    {metadataForm.homeEntityName}
                  </Typography>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item lg={9} xl={9} xs={18}>
          <Card sx={{ height: '100%' }}>
            <Box>
              <CardHeader title={'Description'} />
              <Divider />
            </Box>
            <CardContent>
              <Box sx={{ pt: 2 }}>
                <Typography color="textPrimary" variant="subtitle2">
                  {metadataForm.description || 'No description provided'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
};

MetadataFormInfo.propTypes = {
  metadataForm: PropTypes.any.isRequired,
  visibilityDict: PropTypes.any.isRequired
};
