// Reference tables: straight renames, one staging view each.
const references = {
  stg_ref_sites: {
    source: "ref_sites", key: ["site_code"],
    description: "Sites (fictitious names)",
    columns: { site_code: "Site code (WERKS)", site_name: "Site name", site_org_unit_id: "Site organisational unit" },
  },
  stg_ref_employee_groups: {
    source: "ref_employee_groups", key: ["employee_group_code"],
    description: "Employee groups (PERSG)",
    columns: {
      employee_group_code: "PERSG code", employee_group_label: "CDI, CDD or Alternant",
      contract_category: "permanent, fixed_term or apprentice",
    },
  },
  stg_ref_employee_subgroups: {
    source: "ref_employee_subgroups", key: ["employee_subgroup_code"],
    description: "Employee subgroups / levels (PERSK)",
    columns: { employee_subgroup_code: "PERSK code", employee_subgroup_label: "Level label", level_rank: "1 staff to 3 manager" },
  },
  stg_ref_action_types: {
    source: "ref_action_types", key: ["action_type_code"],
    description: "Personnel action types (MASSN)",
    columns: { action_type_code: "MASSN code", action_type_label: "Label", action_category: "hire, rehire, org_change, contract_change or exit" },
  },
  stg_ref_action_reasons: {
    source: "ref_action_reasons", key: ["action_type_code", "action_reason_code"],
    description: "Personnel action reasons (MASSG) with exit category",
    columns: {
      action_type_code: "MASSN code", action_reason_code: "MASSG code", action_reason_label: "Label",
      exit_category: "resignation, dismissal, mutual_agreement, contract_end or retirement (exits only)",
    },
  },
  stg_ref_absence_types: {
    source: "ref_absence_types", key: ["absence_type_code"],
    description: "Absence types (AWART). counts_in_absenteeism drives the absenteeism numerator.",
    columns: {
      absence_type_code: "AWART code", absence_type_label: "Label", absence_category: "leave, health, family, training or unjustified",
      counts_in_absenteeism: "Included in the absenteeism rate", duration_unit: "working_days or calendar_days",
    },
  },
  stg_ref_calendar: {
    source: "ref_calendar", key: ["calendar_date"],
    description: "One row per day up to the extraction date; metropolitan French public holidays",
    columns: {
      calendar_date: "Day", is_weekend: "Saturday or Sunday", is_public_holiday: "Public holiday (metropolitan France)",
      holiday_name: "Holiday name", is_working_day: "Monday to Friday, not a public holiday",
    },
  },
};

Object.entries(references).forEach(([name, spec]) => {
  publish(name, {
    type: "view",
    schema: "hr_staging",
    tags: ["staging", "reference"],
    description: spec.description,
    columns: spec.columns,
    assertions: { uniqueKey: spec.key, nonNull: spec.key },
  }).query((ctx) => `SELECT ${Object.keys(spec.columns).join(", ")} FROM ${ctx.ref(spec.source)}`);
});
