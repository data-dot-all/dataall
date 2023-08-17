import { ReactiveComponent } from '@appbaseio/reactivesearch';
import { Box } from '@mui/material';
import React from 'react';
import { GlossarySearchUI } from './GlossarySearchUI';

export const GlossarySearchWrapper = (innerClass) => (
  <Box>
    <ReactiveComponent
      componentId="GlossaryPathSensor"
      filterLabel="Glossary"
      innerClass={innerClass}
      defaultQuery={() => ({
        aggs: {
          glossary: {
            terms: {
              field: 'glossary'
            }
          }
        }
      })}
      render={({ aggregations, setQuery }) => {
        let matches = [];
        if (
          aggregations &&
          aggregations.glossary &&
          aggregations.glossary.buckets.length
        ) {
          matches = aggregations.glossary.buckets;
        }
        return <GlossarySearchUI matches={matches} setQuery={setQuery} />;
      }}
    />
  </Box>
);
