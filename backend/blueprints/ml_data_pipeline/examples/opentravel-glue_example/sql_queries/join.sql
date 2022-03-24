select
    A.*, B.website
from
  dhhandsonraw8bc4cveucentral1.airlines_r A
  left join
  dhhandsonraw8bc4cveucentral1.airlines_websites_r B on
  A.pk = B.pk