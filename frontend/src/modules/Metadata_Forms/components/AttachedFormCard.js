import {
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  Typography
} from '@mui/material';

export const AttachedFormCard = (props) => {
  const { fields, attachedForm } = props;

  return (
    <Card sx={{ maxWidth: '600px' }}>
      <CardHeader
        title={attachedForm.metadataForm.name + ' v.' + attachedForm.version}
      ></CardHeader>
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
                {field.value}
              </Typography>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};
