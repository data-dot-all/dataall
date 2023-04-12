import { TableChartOutlined } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Tooltip,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Defaults, Pager } from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { getDatasetSchema, useClient } from '../../services';

const DatasetSchemaItem = (props) => {
  const { table } = props;
  return (
    <Grid item key={table.tableUri} md={3} xs={12} {...props}>
      <Card key={table.tableUri} raised>
        <CardActions
          sx={{
            p: 2
          }}
        >
          <Button
            color="primary"
            startIcon={<TableChartOutlined fontSize="small" />}
            variant="text"
            component={RouterLink}
            to={`/console/datasets/table/${table.tableUri}`}
            sx={{
              overflow: 'hidden',
              pr: 1,
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            <Typography
              sx={{
                width: '200px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                WebkitBoxOrient: 'vertical',
                WebkitLineClamp: 2
              }}
            >
              <Tooltip title={table.GlueTableName}>
                <span>{table.GlueTableName}</span>
              </Tooltip>
            </Typography>
          </Button>
        </CardActions>
        <Divider />
        <CardContent
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            backgroundColor: 'background.default'
          }}
        >
          <Table size="small">
            <TableBody>
              {table && table.columns && table.columns.nodes.length > 0 ? (
                table.columns.nodes.map((column) => (
                  <TableRow>
                    <TableCell>
                      <Typography color="textPrimary" variant="subtitle2">
                        {column.label}{' '}
                        {column.columnType.includes('partition') && (
                          <span>({column.columnType})</span>
                        )}
                      </Typography>
                    </TableCell>

                    <TableCell>
                      <Typography color="textSecondary" variant="body2">
                        {column.typeName}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell>
                    <Typography color="textPrimary" variant="subtitle2">
                      No columns found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
        <Divider />
      </Card>
    </Grid>
  );
};

DatasetSchemaItem.propTypes = {
  table: PropTypes.string.isRequired
};

const DatasetSchemaViewer = (props) => {
  const { dataset } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [loading, setLoading] = useState(true);
  const [tables, setTables] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.selectListFilter);
  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      getDatasetSchema({ datasetUri: dataset.datasetUri, filter })
    );
    if (!response.errors) {
      setTables(response.data.getDataset.tables);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [dataset, client, dispatch, filter]);
  const handlePageChange = async (event, value) => {
    if (value <= tables.pages && value !== tables.page) {
      await setFilter({ ...filter, page: value });
    }
  };
  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!tables) {
    return null;
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        mt: 3
      }}
    >
      {tables.nodes.length > 0 ? (
        <Box>
          <Grid container spacing={3}>
            {tables.nodes.map((node) => (
              <DatasetSchemaItem table={node} />
            ))}
          </Grid>
          <Box>
            <Pager items={tables} onChange={handlePageChange} />
          </Box>
        </Box>
      ) : (
        <Typography color="textPrimary" variant="subtitle2">
          No tables available for this dataset.
        </Typography>
      )}
    </Box>
  );
};
DatasetSchemaViewer.propTypes = {
  dataset: PropTypes.object.isRequired
};
export default DatasetSchemaViewer;
