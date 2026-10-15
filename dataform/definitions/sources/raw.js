// Raw tables loaded by loader/load_raw.py (fictitious data, SAP HCM-inspired structure).
const rawTables = {
  pa0000: "Personnel actions (PA0000-like)",
  pa0001: "Organisational assignment (PA0001-like)",
  pa0002: "Personal data, pseudonymised (PA0002-like)",
  pa0007: "Planned working time (PA0007-like)",
  pa2001: "Absences (PA2001-like)",
  org_units: "Organisational units (flattened, HRP1000/HRP1001-inspired)",
  security_user_scope: "RLS mapping: fictitious user to scope",
  ref_sites: "Sites",
  ref_employee_groups: "Employee groups (PERSG)",
  ref_employee_subgroups: "Employee subgroups / levels (PERSK)",
  ref_action_types: "Personnel action types (MASSN)",
  ref_action_reasons: "Personnel action reasons (MASSG)",
  ref_absence_types: "Absence types (AWART)",
  ref_public_holidays: "Metropolitan French public holidays",
  ref_calendar: "Calendar with working days",
};

Object.entries(rawTables).forEach(([name, description]) =>
  declare({ schema: constants.RAW_DATASET, name, description })
);
