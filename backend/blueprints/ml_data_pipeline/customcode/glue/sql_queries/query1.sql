select
  A.*
from
  {{ ref("localfilesample")}} A
  inner join
  {{ ref("localfilesample2")}} B on
  A.id = B.id
where
  A.job like '%broker%'
