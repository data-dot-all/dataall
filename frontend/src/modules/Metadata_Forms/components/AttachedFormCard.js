import { Card, CardContent } from '@mui/material';

export const AttachedFormCard = (props) => {
  const { fields } = props;

  return (
    <Card>
      {fields.map((field) => (
        <CardContent>
          {field.field.name}
          {field.value}
        </CardContent>
      ))}
    </Card>
  );
};
