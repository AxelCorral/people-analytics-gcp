// Shared constants for SQLX models.
const vars = dataform.projectConfig.vars;

// SAP open-end sentinel. Converted to NULL in staging, re-applied only inside range joins.
const OPEN_END = "DATE '9999-12-31'";

const RAW_DATASET = vars.raw_dataset;
const SNAPSHOT_START_DATE = vars.snapshot_start_date;
const LOOKBACK_DAYS = Number(vars.lookback_days);

// `d BETWEEN valid_from AND valid_to` with a NULL (open) valid_to
function inPeriod(d, from, to) {
  return `${d} BETWEEN ${from} AND COALESCE(${to}, ${OPEN_END})`;
}

module.exports = { OPEN_END, RAW_DATASET, SNAPSHOT_START_DATE, LOOKBACK_DAYS, inPeriod };
