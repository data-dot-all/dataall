import { ReactiveComponent } from '@appbaseio/reactivesearch';
import { Box } from '@mui/material';
import React from 'react';
import { GlossarySearch } from './GlossarySearch';

export const GlossarySearchComponent = (innerClass) => (
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
        return <GlossarySearch matches={matches} setQuery={setQuery} />;
      }}
    />
  </Box>
);
