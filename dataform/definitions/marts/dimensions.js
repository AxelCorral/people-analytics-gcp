// Small dimensions of the star schema (Power BI import).
const marts = { type: "table", schema: "hr_marts" };

publish("dim_date", {
  ...marts,
  tags: ["marts"],
  description: "Date dimension, from the start of the reporting window to the extraction date (no future date).",
  columns: {
    date: "Day (key)", year: "Year", quarter: "Quarter number", month: "Month number",
    month_start: "First day of the month", month_end: "Last day of the month",
    year_month: "YYYY-MM", month_label: "Month name (French) and year", month_short_fr: "Short French month name",
    is_month_end: "Last day of the month", is_working_day: "Working day (metropolitan France)",
    is_public_holiday: "Public holiday", holiday_name: "Holiday name",
  },
  assertions: { uniqueKey: ["date"], nonNull: ["date", "month_start"] },
}).query((ctx) => `
  SELECT
    c.calendar_date AS date,
    c.calendar_year AS year,
    c.calendar_quarter AS quarter,
    c.calendar_month AS month,
    c.month_start,
    c.month_end,
    FORMAT_DATE('%Y-%m', c.calendar_date) AS year_month,
    CONCAT(m.name, ' ', CAST(c.calendar_year AS STRING)) AS month_label,
    m.short AS month_short_fr,
    c.is_month_end,
    c.is_working_day,
    c.is_public_holiday,
    c.holiday_name
  FROM ${ctx.ref("int_calendar")} AS c
  CROSS JOIN ${ctx.ref("int_extraction_context")} AS x
  JOIN UNNEST([
    STRUCT(1 AS n, 'janvier' AS name, 'janv.' AS short), (2, 'février', 'févr.'), (3, 'mars', 'mars'),
    (4, 'avril', 'avr.'), (5, 'mai', 'mai'), (6, 'juin', 'juin'), (7, 'juillet', 'juil.'), (8, 'août', 'août'),
    (9, 'septembre', 'sept.'), (10, 'octobre', 'oct.'), (11, 'novembre', 'nov.'), (12, 'décembre', 'déc.')
  ]) AS m ON m.n = c.calendar_month
  WHERE c.calendar_date BETWEEN x.snapshot_start_date AND x.as_of_date
`);

publish("dim_org_unit", {
  ...marts,
  tags: ["marts"],
  description: "Departments (grain of every fact) with their site. Target of the RLS filter.",
  columns: {
    org_unit_id: "Department org unit (key)", department_code: "D01 to D12", department_name: "Department name",
    site_code: "Site code", site_name: "Site name", site_org_unit_id: "Site org unit",
    head_employee_id: "Head of department at the extraction date",
  },
  assertions: { uniqueKey: ["org_unit_id"], nonNull: ["org_unit_id", "site_code", "department_name"] },
}).query((ctx) => `
  SELECT
    d.org_unit_id,
    d.department_code,
    d.org_unit_name AS department_name,
    d.site_code,
    s.site_name,
    d.parent_org_unit_id AS site_org_unit_id,
    d.head_employee_id
  FROM ${ctx.ref("stg_org_units")} AS d
  JOIN ${ctx.ref("stg_ref_sites")} AS s USING (site_code)
  WHERE d.org_unit_level = 'department'
`);

publish("dim_employee", {
  ...marts,
  tags: ["marts", "pii"],
  description: "Employees (pseudonyms). current_org_unit_id = department at the extraction date (last department for leavers), used by the RLS filter on this table.",
  columns: {
    employee_id: "Personnel number (key)", display_name: "Pseudonym 'Salarié 000123'",
    gender_code: "1 male, 2 female", gender_label: "Femme / Homme", birth_date: "Date of birth (fictitious)",
    nationality_code: "ISO 3166-1 alpha-2", first_hire_date: "First hire date",
    current_org_unit_id: "Department at the extraction date", current_site_code: "Site at the extraction date",
    current_employee_group_code: "PERSG at the extraction date", current_employee_subgroup_code: "PERSK at the extraction date",
    is_active_at_extraction: "Employed at the extraction date",
    org_unit_ids_history: "Departments where the employee worked in the reporting window, '|id1|id2|' (RLS on this table)",
    site_codes_history: "Sites where the employee worked in the reporting window, '|S100|S200|' (RLS on this table)",
  },
  assertions: { uniqueKey: ["employee_id"], nonNull: ["employee_id", "display_name", "current_org_unit_id"] },
}).query((ctx) => `
  WITH history AS (
    SELECT
      p.employee_id,
      CONCAT('|', STRING_AGG(DISTINCT p.org_unit_id, '|' ORDER BY p.org_unit_id), '|') AS org_unit_ids_history,
      CONCAT('|', STRING_AGG(DISTINCT p.site_code, '|' ORDER BY p.site_code), '|') AS site_codes_history
    FROM ${ctx.ref("int_employee_periods")} AS p
    CROSS JOIN ${ctx.ref("int_extraction_context")} AS x
    WHERE p.is_active
      AND p.period_start <= x.as_of_date
      AND COALESCE(p.period_end, ${constants.OPEN_END}) >= x.snapshot_start_date
    GROUP BY p.employee_id
  ),
  current_period AS (
    SELECT p.*
    FROM ${ctx.ref("int_employee_periods")} AS p
    CROSS JOIN ${ctx.ref("int_extraction_context")} AS x
    WHERE ${constants.inPeriod("x.as_of_date", "p.period_start", "p.period_end")}
  ),
  first_hire AS (
    SELECT employee_id, MIN(spell_start) AS first_hire_date
    FROM ${ctx.ref("int_employment_spells")}
    GROUP BY employee_id
  )
  SELECT
    e.employee_id,
    e.display_name,
    e.gender_code,
    e.gender_label,
    e.birth_date,
    e.nationality_code,
    f.first_hire_date,
    c.org_unit_id AS current_org_unit_id,
    c.site_code AS current_site_code,
    c.employee_group_code AS current_employee_group_code,
    c.employee_subgroup_code AS current_employee_subgroup_code,
    c.is_active AS is_active_at_extraction,
    COALESCE(h.org_unit_ids_history, '|') AS org_unit_ids_history,
    COALESCE(h.site_codes_history, '|') AS site_codes_history
  FROM ${ctx.ref("stg_pa0002_persons")} AS e
  JOIN current_period AS c USING (employee_id)
  LEFT JOIN first_hire AS f USING (employee_id)
  LEFT JOIN history AS h USING (employee_id)
`);

publish("dim_contract_type", {
  ...marts,
  tags: ["marts"],
  description: "Contract types (PERSG).",
  columns: { employee_group_code: "PERSG (key)", contract_type: "CDI, CDD, Alternant", contract_category: "permanent, fixed_term, apprentice" },
  assertions: { uniqueKey: ["employee_group_code"] },
}).query((ctx) => `
  SELECT employee_group_code, employee_group_label AS contract_type, contract_category
  FROM ${ctx.ref("stg_ref_employee_groups")}
`);

publish("dim_level", {
  ...marts,
  tags: ["marts"],
  description: "Employee levels (PERSK).",
  columns: { employee_subgroup_code: "PERSK (key)", level_label: "Cadre, Agent de maîtrise, Employé / ouvrier", level_rank: "1 to 3" },
  assertions: { uniqueKey: ["employee_subgroup_code"] },
}).query((ctx) => `
  SELECT employee_subgroup_code, employee_subgroup_label AS level_label, level_rank
  FROM ${ctx.ref("stg_ref_employee_subgroups")}
`);

publish("dim_absence_type", {
  ...marts,
  tags: ["marts"],
  description: "Absence types. counts_in_absenteeism separates the absenteeism rate from total absences (paid leave included).",
  columns: {
    absence_type_code: "AWART (key)", absence_type_label: "Label", absence_category: "leave, health, family, training, unjustified",
    counts_in_absenteeism: "Included in the absenteeism rate", absence_scope: "« Absentéisme » or « Autres absences (congés inclus) »",
  },
  assertions: { uniqueKey: ["absence_type_code"] },
}).query((ctx) => `
  SELECT
    absence_type_code,
    absence_type_label,
    absence_category,
    counts_in_absenteeism,
    IF(counts_in_absenteeism, 'Absentéisme', 'Autres absences (congés inclus)') AS absence_scope
  FROM ${ctx.ref("stg_ref_absence_types")}
`);

publish("dim_action_type", {
  ...marts,
  tags: ["marts"],
  description: "Personnel action type and reason, with the exit category.",
  columns: {
    action_key: "MASSN-MASSG (key)", action_type_code: "MASSN", action_type_label: "Action label",
    action_category: "hire, rehire, org_change, contract_change, exit", action_reason_code: "MASSG",
    action_reason_label: "Reason label", exit_category: "Exit category (exits only)", exit_category_label: "French label of the exit category",
  },
  assertions: { uniqueKey: ["action_key"] },
}).query((ctx) => `
  SELECT
    CONCAT(r.action_type_code, '-', r.action_reason_code) AS action_key,
    r.action_type_code,
    t.action_type_label,
    t.action_category,
    r.action_reason_code,
    r.action_reason_label,
    r.exit_category,
    CASE r.exit_category
      WHEN 'resignation' THEN 'Démission'
      WHEN 'dismissal' THEN 'Licenciement'
      WHEN 'mutual_agreement' THEN 'Rupture conventionnelle'
      WHEN 'contract_end' THEN 'Fin de contrat'
      WHEN 'retirement' THEN 'Retraite'
    END AS exit_category_label
  FROM ${ctx.ref("stg_ref_action_reasons")} AS r
  JOIN ${ctx.ref("stg_ref_action_types")} AS t USING (action_type_code)
`);

publish("sec_user_scope", {
  ...marts,
  tags: ["marts", "security"],
  description: "RLS table: fictitious UPN to scope. Disconnected and hidden in the Power BI model.",
  columns: { user_upn: "UPN (@example.com)", scope_type: "ALL, SITE, DEPT", scope_value: "'*', site code or department org unit id", role_label: "Business role" },
  assertions: { uniqueKey: ["user_upn", "scope_type", "scope_value"] },
}).query((ctx) => `
  SELECT user_upn, scope_type, scope_value, role_label FROM ${ctx.ref("stg_security_user_scope")}
`);
