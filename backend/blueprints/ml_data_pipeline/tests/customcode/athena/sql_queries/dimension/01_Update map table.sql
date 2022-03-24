INSERT INTO {{model_name}}.{{dimension}}

WITH examplevalue AS
(
	SELECT DISTINCT
		id
	FROM {{source_database}}.v_{{dimension}}
)

.....