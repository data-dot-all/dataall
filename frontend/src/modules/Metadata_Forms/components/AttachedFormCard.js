import {
  Card,
  CardContent,
  CardHeader,
  Grid,
  List,
  ListItem,
  Typography
} from '@mui/material';
import { PencilAltIcon } from 'design';
import React from 'react';

export const AttachedFormCard = (props) => {
  const { fields, attachedForm, onEdit, editable } = props;

  return (
    <Card sx={{ maxWidth: '600px' }}>
      <Grid container spacing={2}>
        <Grid item lg={10} xl={10} xs={20}>
          <CardHeader
            title={
              attachedForm.metadataForm.name + ' v.' + attachedForm.version
            }
          ></CardHeader>
        </Grid>
        <Grid
          item
          lg={2}
          xl={2}
          xs={4}
          sx={{ textAlign: 'right', pr: 2, mt: 2 }}
        >
          {editable && (
            <PencilAltIcon
              sx={{ color: 'primary.main', opacity: 0.5 }}
              onMouseOver={(e) => {
                e.currentTarget.style.opacity = 1;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = 0.5;
              }}
              onClick={onEdit}
            />
          )}
        </Grid>
      </Grid>

      <CardContent>
        <List>
          {fields.map((field) => (
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
                {field.field.name}
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
                {field.value?.toString()}
              </Typography>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};
