import PropTypes from 'prop-types';
import { Box, Card, CardContent, CardHeader, Divider, List, ListItem, Typography } from '@material-ui/core';
import React from 'react';
import Scrollbar from '../../components/Scrollbar';

const TableGlueProperties = (props) => {
  const {
    glueProperties,
    ...other } = props;

  return (
    <Card
      {...other}
      sx={{ height: '500px'
      }}
    >
      <CardHeader
        title="Glue Properties"
      />
      <Divider />
      <Scrollbar options={{ suppressScrollX: true }}>
        <CardContent sx={{ pt: 0 }}>
          {glueProperties
                && (
                <Box sx={{ mt: 3 }}>
                  <List>
                    {
                      Object.entries(JSON.parse(glueProperties)).map(([key, value]) => (
                        <ListItem
                          disableGutters
                          divider
                          sx={{
                            justifyContent: 'space-between',
                            padding: 2
                          }}
                        >
                          <Typography
                            color="textSecondary"
                            variant="subtitle2"
                          >
                            {key}
                          </Typography>
                          <Typography
                            color="textPrimary"
                            variant="body2"
                          >
                            {value}
                          </Typography>
                        </ListItem>
                      ))
                  }
                  </List>
                </Box>
                )}
        </CardContent>
      </Scrollbar>
    </Card>
  );
};

TableGlueProperties.propTypes = {
  glueProperties: PropTypes.string.isRequired
};

export default TableGlueProperties;
