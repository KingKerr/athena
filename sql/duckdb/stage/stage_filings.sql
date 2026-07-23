create table if not exists stage_risk_factor (
  ticker text,
  cik text,
  company_name text,
  filing_date date,
  form_type text,
  accession_number text,
  primary_category text,
  secondary_category text,
  tertiary_category text,
  supporting_text text,
  raw_json text
);

create table if not exists stage_filing_section (
  ticker text,
  cik text,
  company_name text,
  filing_date date,
  form_type text,
  accession_number text,
  section_name text,
  section_text text,
  raw_json text
);