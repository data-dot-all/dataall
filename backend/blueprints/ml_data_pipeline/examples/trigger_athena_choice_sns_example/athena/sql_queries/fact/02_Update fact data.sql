INSERT INTO {{model_name}}.{{fact}}

WITH examplevalue AS
(
	SELECT DISTINCT
		id
	FROM {{source_database}}.v_{{fact}}
)

.....