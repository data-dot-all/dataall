select
    A.*, B.start,B.end
from
  "pipeline-test-24-06-eu-central-1-10eff4b2"."cannes_winner_csv_filtered" A
  left join
    "pipeline-test-24-06-eu-central-1-10eff4b2"."cannes_festival_dates_csv_filtered" B on
  A.year = B.year
