States.Format('ALTER TABLE {{model_name}}.fact_{{fact}} SET LOCATION "s3://{{bucket_name}}/fact_{{fact}}/{}/"',{{execution_id}})
