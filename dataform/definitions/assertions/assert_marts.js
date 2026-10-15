// Mart-level consistency checks.

assert("assert_snapshot_matches_spells", {
  tags: ["assertions", "marts"],
  description: "At every month end, the daily snapshot has exactly one row per open employment spell.",
}).query((ctx) => `
  WITH month_ends AS (
    SELECT date FROM ${ctx.ref("dim_date")} WHERE is_month_end
  ),
  snapshot AS (
    SELECT snapshot_date AS date, COUNT(*) AS n FROM ${ctx.ref("fct_headcount_daily")} GROUP BY 1
  ),
  spells AS (
    SELECT m.date, COUNT(s.spell_id) AS n
    FROM month_ends AS m
    LEFT JOIN ${ctx.ref("int_employment_spells")} AS s
      ON ${constants.inPeriod("m.date", "s.spell_start", "s.spell_last_day")}
    GROUP BY 1
  )
  SELECT sp.date, sp.n AS open_spells, COALESCE(sn.n, 0) AS snapshot_rows
  FROM spells AS sp
  LEFT JOIN snapshot AS sn USING (date)
  WHERE sp.n != COALESCE(sn.n, 0)
`);

assert("assert_no_future_dates", {
  tags: ["assertions", "marts"],
  description: "No fact or dimension date after the extraction date.",
}).query((ctx) => `
  WITH dates AS (
    SELECT 'dim_date' AS model, MAX(date) AS max_date FROM ${ctx.ref("dim_date")}
    UNION ALL SELECT 'fct_headcount_daily', MAX(snapshot_date) FROM ${ctx.ref("fct_headcount_daily")}
    UNION ALL SELECT 'fct_headcount_monthly', MAX(month_end_date) FROM ${ctx.ref("fct_headcount_monthly")}
    UNION ALL SELECT 'fct_movements', MAX(event_date) FROM ${ctx.ref("fct_movements")}
    UNION ALL SELECT 'fct_worktime_monthly', MAX(month_start) FROM ${ctx.ref("fct_worktime_monthly")}
    UNION ALL SELECT 'fct_absence_monthly', MAX(month_start) FROM ${ctx.ref("fct_absence_monthly")}
    UNION ALL SELECT 'rpt_kpi_monthly', MAX(month_end_date) FROM ${ctx.ref("rpt_kpi_monthly")}
  )
  SELECT d.model, d.max_date, x.as_of_date
  FROM dates AS d
  CROSS JOIN ${ctx.ref("int_extraction_context")} AS x
  WHERE d.max_date > x.as_of_date
`);

assert("assert_movements_balance_headcount", {
  tags: ["assertions", "marts"],
  description: "Company level: headcount change between consecutive month ends equals entries minus exits. An exit leaves the headcount the day AFTER its last worked day, so it is dated BEGDA (= last day + 1) here, unlike the exit KPI (dated on the last worked day).",
}).query((ctx) => `
  WITH heads AS (
    SELECT month_start, headcount, LAG(headcount) OVER (ORDER BY month_start) AS previous_headcount
    FROM ${ctx.ref("rpt_kpi_monthly")}
    WHERE scope_level = 'company'
  ),
  flows AS (
    SELECT
      DATE_TRUNC(IF(is_exit, DATE_ADD(event_date, INTERVAL 1 DAY), event_date), MONTH) AS month_start,
      COUNTIF(is_entry) - COUNTIF(is_exit) AS net_flow
    FROM ${ctx.ref("fct_movements")}
    WHERE is_entry OR is_exit
    GROUP BY 1
  )
  SELECT h.month_start, h.previous_headcount, h.headcount, COALESCE(f.net_flow, 0) AS net_flow
  FROM heads AS h
  LEFT JOIN flows AS f USING (month_start)
  WHERE h.previous_headcount IS NOT NULL
    AND h.headcount - h.previous_headcount != COALESCE(f.net_flow, 0)
`);
