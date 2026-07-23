import duckdb
from pipelines.ingestion.common import get_duckdb_path

db_path = get_duckdb_path()
print("DB path:", db_path)

con = duckdb.connect(db_path)

print("Tables:")
print(con.execute("show tables;").fetchall())

print("Row counts:")
print(con.execute("""
select table_name, row_count
from (
  select 'stage_price_daily' as table_name, count(*) as row_count from stage_price_daily
  union all
  select 'stage_news', count(*) from stage_news
  union all
  select 'stage_filing_section', count(*) from stage_filing_section
  union all
  select 'stage_risk_factor', count(*) from stage_risk_factor
  union all
  select 'mart_fact_price_daily', count(*) from mart_fact_price_daily
  union all
  select 'mart_fact_news', count(*) from mart_fact_news
  union all
  select 'mart_fact_filing_section', count(*) from mart_fact_filing_section
  union all
  select 'mart_fact_risk_factor', count(*) from mart_fact_risk_factor
) t
order by table_name;
""").fetchall())