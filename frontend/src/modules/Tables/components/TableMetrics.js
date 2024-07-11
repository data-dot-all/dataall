import { useTheme } from '@emotion/react';
import { PlayArrowOutlined, RefreshRounded } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  MenuItem,
  MenuList,
  Tooltip,
  Typography
} from '@mui/material';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import Chart from 'react-apexcharts';
import { CgHashtag } from 'react-icons/cg';
import { VscSymbolString } from 'react-icons/vsc';
import { Label, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  getDatasetTableProfilingRun,
  listDatasetTableProfilingRuns,
  startDatasetProfilingRun
} from '../services';

export const TableMetrics = ({ table, isAdmin }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const theme = useTheme();
  const [ready, setReady] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [column, setColumn] = useState(null);
  const [profiling, setProfiling] = useState(null);
  const [activeItem, setActiveItem] = useState(null);
  const [profilingStatus, setProfilingStatus] = useState('-');
  const valueDistributionChart = {
    options: {
      chart: {
        id: 'basic-bar',
        background: 'transparent',
        stacked: true
      },
      dataLabels: {
        enabled: false
      },
      grid: {
        borderColor: theme.palette.divider,
        yaxis: {
          lines: {
            show: false
          }
        }
      },
      legend: {
        show: false
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: 45,
          distributed: true
        }
      },
      theme: {
        mode: theme.palette.mode
      },
      xaxis: {
        categories: ['StdDev', 'Max', 'Mean', 'Min']
      }
    },
    series: [
      {
        name: 'Value Distribution',
        data: [
          column?.Metadata?.StdDeviation ? column?.Metadata?.StdDeviation : 0,
          column?.Metadata?.Maximum ? column?.Metadata?.Maximum : 0,
          column?.Metadata?.Mean ? column?.Metadata?.Mean : 0,
          column?.Metadata?.Minimum ? column?.Metadata?.Minimum : 0
        ]
      }
    ]
  };

  const histogramChart = {
    options: {
      chart: {
        id: 'basic-bar',
        background: 'transparent',
        stacked: false
      },
      dataLabels: {
        enabled: false
      },
      grid: {
        borderColor: theme.palette.divider,
        yaxis: {
          lines: {
            show: false
          }
        }
      },
      legend: {
        show: false
      },
      plotOptions: {
        bar: {
          vertical: true,
          barHeight: 45,
          distributed: true
        }
      },
      theme: {
        mode: theme.palette.mode
      },
      xaxis: {
        categories: column?.Metadata?.Histogram.map((r) => r.value)
      }
    },
    series: [
      {
        name: 'Histogram',
        data: column?.Metadata?.Histogram.map((r) => r.count)
      }
    ]
  };

  const handleItemClick = (columnName, index) => {
    setActiveItem(index);
    setColumn(metrics.columns.filter((obj) => obj.Name === columnName)[0]);
  };
  const statusColor = (status) => {
    let color = 'blue';
    switch (status) {
      case 'SUCCEEDED':
        color = 'success';
        break;
      case 'UNKNOWN':
      case 'FAILED':
      case 'STOPPED':
        color = 'error';
        break;
      case 'RUNNING':
        color = 'primary';
        break;
      default:
        color = 'primary';
    }
    return color;
  };

  const fetchData = useCallback(async () => {
    setReady(false);
    const response = await client.query(
      getDatasetTableProfilingRun(table.tableUri)
    );
    if (!response.errors) {
      if (response.data.getDatasetTableProfilingRun) {
        setProfilingStatus(response.data.getDatasetTableProfilingRun.status);
        if (response.data.getDatasetTableProfilingRun.results) {
          const res = JSON.parse(
            response.data.getDatasetTableProfilingRun.results
          );
          setMetrics(res);
          setColumn(res?.columns[0]);
          setActiveItem(res?.columns[0]?.Name);
        }
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setReady(true);
  }, [client, dispatch, table.tableUri]);

  const listProfilingRuns = useCallback(async () => {
    const response = await client.query(
      listDatasetTableProfilingRuns(table.tableUri)
    );
    if (!response.errors) {
      if (
        response.data.listDatasetTableProfilingRuns &&
        response.data.listDatasetTableProfilingRuns.nodes.length > 0
      ) {
        setProfilingStatus(
          response.data.listDatasetTableProfilingRuns.nodes[0].status
        );
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, table.tableUri]);

  const startProfilingRun = async () => {
    try {
      setProfiling(true);
      const response = await client.mutate(
        startDatasetProfilingRun({
          input: { datasetUri: table.datasetUri, tableUri: table.tableUri }
        })
      );
      if (!response.errors) {
        await listProfilingRuns();
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setProfiling(false);
    }
  };

  useEffect(() => {
    if (client) {
      listProfilingRuns().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchData().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, listProfilingRuns, fetchData, dispatch]);
  if (!ready) {
    return (
      <div
        style={{
          width: '1fr',
          display: 'block',
          height: '100%'
        }}
      >
        <CircularProgress />
      </div>
    );
  }
  const buildPercentValue = (number) => {
    if (number % 1 === 0) {
      return number * 100;
    }

    return (number * 100).toFixed(3);
  };
  return (
    <Box>
      <Grid container spacing={6} wrap="wrap">
        <Grid item md={9} sm={6} xs={12} />
        {isAdmin && (
          <Grid item md={3} sm={6} xs={12}>
            <Box sx={{ m: -1, mb: 2, ml: 10 }}>
              <Button
                color="primary"
                startIcon={<RefreshRounded fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
                onClick={fetchData}
              >
                Refresh
              </Button>
              <LoadingButton
                loading={profiling}
                color="primary"
                onClick={startProfilingRun}
                startIcon={<PlayArrowOutlined fontSize="small" />}
                sx={{ m: 1 }}
                variant="contained"
              >
                Profile
              </LoadingButton>
            </Box>
          </Grid>
        )}
      </Grid>
      <Card>
        <Grid container>
          <Grid
            item
            md={3}
            xs={12}
            sx={{
              alignItems: 'center',
              borderRight: (th) => ({
                md: `1px solid ${th.palette.divider}`
              }),
              borderBottom: (th) => ({
                md: 'none',
                xs: `1px solid ${th.palette.divider}`
              }),
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                Rows
              </Typography>
              <Typography color="textPrimary" variant="h5">
                {metrics?.table_nb_rows || '-'}
              </Typography>
            </div>
          </Grid>
          <Grid
            item
            md={3}
            xs={12}
            sx={{
              alignItems: 'center',
              borderRight: (th) => ({
                md: `1px solid ${th.palette.divider}`
              }),
              borderBottom: (th) => ({
                xs: `1px solid ${th.palette.divider}`,
                md: 'none'
              }),
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                Columns
              </Typography>
              <Typography color="textPrimary" variant="h5">
                {metrics?.columns.length || '-'}
              </Typography>
            </div>
          </Grid>
          <Grid
            item
            md={3}
            xs={12}
            sx={{
              alignItems: 'center',
              borderRight: (th) => ({
                md: `1px solid ${th.palette.divider}`
              }),
              borderBottom: (th) => ({
                xs: `1px solid ${th.palette.divider}`,
                md: 'none'
              }),
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                Data Types
              </Typography>
              <Typography color="textPrimary" variant="h5">
                {metrics?.dataTypes.length || '-'}
              </Typography>
            </div>
          </Grid>
          <Grid
            item
            md={3}
            xs={12}
            sx={{
              alignItems: 'center',
              display: 'flex',
              justifyContent: 'space-between',
              p: 3
            }}
          >
            <div>
              <Typography color="textSecondary" variant="overline">
                Last job run
              </Typography>
              <Typography color="textPrimary" variant="h5">
                <Label color={statusColor(profilingStatus)}>
                  {profilingStatus}
                </Label>
              </Typography>
            </div>
          </Grid>
        </Grid>
      </Card>
      <Grid container spacing={2}>
        <Grid
          item
          md={3}
          xs={12}
          sx={{
            mt: 2
          }}
        >
          {metrics && metrics.columns && (
            <Card>
              <Scrollbar options={{ suppressScrollX: false }}>
                <MenuList>
                  {metrics.columns.map((col, index) => (
                    <Box>
                      <MenuItem
                        key={col.columnUri}
                        onClick={() => {
                          handleItemClick(col.Name, index);
                        }}
                        selected={activeItem === index}
                      >
                        {col.Type !== 'String' ? (
                          <IconButton>
                            <CgHashtag />
                          </IconButton>
                        ) : (
                          <IconButton>
                            <VscSymbolString />
                          </IconButton>
                        )}
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
                          <Tooltip title={col.Name}>
                            <span>{col.Name.substring(0, 22)}</span>
                          </Tooltip>
                        </Typography>
                      </MenuItem>
                    </Box>
                  ))}
                </MenuList>
              </Scrollbar>
            </Card>
          )}
        </Grid>
        {column && (
          <Grid
            item
            md={9}
            xs={12}
            sx={{
              mt: 2
            }}
          >
            <Box
              sx={{
                backgroundColor: 'background.default'
              }}
            >
              <Card sx={{ mb: 2 }}>
                <CardHeader
                  title={
                    <Typography color="textPrimary" variant="h5">
                      {column.Name}
                    </Typography>
                  }
                  subheader={column.Type}
                />
              </Card>
              <Card sx={{ mb: 2 }}>
                <CardHeader title="Data Quality" />
                <Divider />
                <Box sx={{ p: 2 }} alignItems="center">
                  <LinearProgress
                    sx={{ height: 10, borderRadius: 5 }}
                    variant="determinate"
                    value={Math.trunc(column?.Metadata?.Completeness * 100)}
                  />
                </Box>
                <Grid container spacing={2}>
                  <Grid
                    item
                    md={9}
                    xs={12}
                    sx={{
                      mt: 1
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        ml: 3,
                        mb: 2
                      }}
                    >
                      <Chip
                        color="primary"
                        label={buildPercentValue(
                          column?.Metadata?.Completeness
                        )}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Typography color="textSecondary" variant="subtitle2">
                        VALID VALUES
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid
                    item
                    md={3}
                    xs={12}
                    sx={{
                      mt: 1
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        ml: 3,
                        mb: 2
                      }}
                    >
                      <Chip
                        color="primary"
                        label={buildPercentValue(
                          1 - column?.Metadata?.Completeness
                        )}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Typography color="textSecondary" variant="subtitle2">
                        MISSING VALUES
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Card>
              {column && column.Type !== 'String' && (
                <Card>
                  <CardHeader title="Value Distribution" />
                  <Divider />
                  <Chart
                    height="350"
                    type="bar"
                    options={valueDistributionChart.options}
                    series={valueDistributionChart.series}
                  />

                  <CardContent />
                </Card>
              )}

              <Card sx={{ mt: 2 }}>
                <CardHeader title="Histogram" />
                <Divider />
                <CardContent>
                  {column.Metadata?.Histogram.length > 0 ? (
                    <Chart
                      height="350"
                      type="bar"
                      options={histogramChart.options}
                      series={histogramChart.series}
                    />
                  ) : (
                    <Typography color="textPrimary" variant="subtitle2">
                      No histogram data available.
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

TableMetrics.propTypes = {
  table: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
