import { Card, CircularProgress } from '@mui/material';
import { styled } from '@mui/styles';
import { DataGrid } from '@mui/x-data-grid';
import * as PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as ReactIf from 'react-if';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { previewTable } from '../services';

const StyledDataGrid = styled(DataGrid)(({ theme }) => ({
  '& .MuiDataGrid-columnsContainer': {
    backgroundColor:
      theme.palette.mode === 'dark'
        ? 'rgba(29,29,29,0.33)'
        : 'rgba(255,255,255,0.38)'
  }
}));
export const TablePreview = (props) => {
  const { table } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState({ rows: [], fields: [] });
  const fetchData = useCallback(async () => {
    setRunning(true);
    const response = await client.query(previewTable(table.tableUri));
    if (!response.errors) {
      setResult(response.data.previewTable);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setRunning(false);
  }, [client, dispatch, table.tableUri]);

  const buildRows = (rows, fields) => {
    const header = fields.map((field) => JSON.parse(field).name);
    const newRows = rows.map((row) => JSON.parse(row));
    const builtRows = newRows.map((row) =>
      header.map((h, index) => ({ [h]: row[index] }))
    );
    const objects = [];
    builtRows.forEach((row) => {
      const obj = {};
      row.forEach((r) => {
        Object.entries(r).forEach(([key, value]) => {
          obj[key] = value;
        });
        obj.id = Math.random();
      });
      objects.push(obj);
    });
    return objects;
  };

  const buildHeader = (fields) =>
    fields.map((field) => ({
      field: JSON.parse(field).name,
      headerName: JSON.parse(field).name,
      editable: false
    }));

  useEffect(() => {
    if (client) {
      fetchData().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchData, dispatch]);

  return (
    <ReactIf.If condition={running}>
      <ReactIf.Then>
        <CircularProgress />
      </ReactIf.Then>
      <ReactIf.Else>
        <Card sx={{ height: 700 }}>
          <StyledDataGrid
            disableColumnResize={false}
            disableColumnReorder={false}
            rows={buildRows(result.rows, result.fields)}
            columns={buildHeader(result.fields)}
          />
        </Card>
      </ReactIf.Else>
    </ReactIf.If>
  );
};

TablePreview.propTypes = {
  table: PropTypes.object.isRequired
};
