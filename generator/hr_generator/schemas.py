"""Explicit schemas of the raw tables (reused later for the BigQuery load)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    type: str  # STRING | DATE | INT64 | FLOAT64 | BOOL | TIMESTAMP
    description: str
    required: bool = True


META = [
    Column("_batch_id", "STRING", "Generator run identifier (seed and as-of date)"),
    Column("_extracted_at", "TIMESTAMP", "Simulated extraction timestamp (day after the as-of date)"),
]

KEY = [
    Column("PERNR", "STRING", "Personnel number (8 digits)"),
    Column("BEGDA", "DATE", "Validity start date"),
    Column("ENDDA", "DATE", "Validity end date, 9999-12-31 when open"),
]

SCHEMAS: dict[str, list[Column]] = {
    "pa0000": KEY + [
        Column("MASSN", "STRING", "Action type (project code, see ref_action_types)"),
        Column("MASSG", "STRING", "Action reason (project code, see ref_action_reasons)"),
        Column("STAT2", "STRING", "Employment status: 3 active, 0 withdrawn"),
    ],
    "pa0001": KEY + [
        Column("BUKRS", "STRING", "Company code (fictitious)"),
        Column("WERKS", "STRING", "Personnel area, used as site code"),
        Column("BTRTL", "STRING", "Personnel subarea"),
        Column("PERSG", "STRING", "Employee group: 1 CDI, 2 CDD, 3 apprentice"),
        Column("PERSK", "STRING", "Employee subgroup / level: CA, AM, EO"),
        Column("ORGEH", "STRING", "Organisational unit"),
        Column("PLANS", "STRING", "Position, 99999999 after an exit"),
        Column("STELL", "STRING", "Job key"),
        Column("KOSTL", "STRING", "Cost center"),
    ],
    "pa0002": KEY + [
        Column("NACHN", "STRING", "Last name: pseudonym, always 'Salarié'"),
        Column("VORNA", "STRING", "First name: pseudonym, 6-digit sequence"),
        Column("GBDAT", "DATE", "Date of birth (fictitious)"),
        Column("GESCH", "STRING", "Gender key: 1 male, 2 female"),
        Column("NATIO", "STRING", "Nationality (ISO 3166-1 alpha-2)"),
    ],
    "pa0007": KEY + [
        Column("SCHKZ", "STRING", "Work schedule rule (project code)"),
        Column("EMPCT", "FLOAT64", "Employment percentage"),
        Column("WOSTD", "FLOAT64", "Weekly working hours"),
    ],
    "pa2001": KEY + [
        Column("AWART", "STRING", "Absence type (project code, see ref_absence_types)"),
        Column("ABWTG", "FLOAT64", "Absence working days"),
        Column("STDAZ", "FLOAT64", "Absence hours"),
    ],
    "org_units": [
        Column("org_unit_id", "STRING", "Organisational unit id (= ORGEH)"),
        Column("org_unit_name", "STRING", "Organisational unit name"),
        Column("org_unit_level", "STRING", "company, site or department"),
        Column("parent_org_unit_id", "STRING", "Parent unit", required=False),
        Column("site_code", "STRING", "Site code (= WERKS)", required=False),
        Column("department_code", "STRING", "Department code", required=False),
        Column("head_pernr", "STRING", "Head of unit at the as-of date", required=False),
        Column("valid_from", "DATE", "Validity start date"),
        Column("valid_to", "DATE", "Validity end date"),
    ],
    "security_user_scope": [
        Column("user_upn", "STRING", "Fictitious user principal name (@example.com)"),
        Column("scope_type", "STRING", "ALL, SITE or DEPT"),
        Column("scope_value", "STRING", "'*', site code or org unit id"),
        Column("role_label", "STRING", "Business role"),
    ],
    "ref_sites": [
        Column("site_code", "STRING", "Site code"),
        Column("site_name", "STRING", "Site name (fictitious)"),
        Column("site_org_unit_id", "STRING", "Site organisational unit"),
    ],
    "ref_employee_groups": [
        Column("employee_group_code", "STRING", "PERSG code"),
        Column("employee_group_label", "STRING", "Label"),
        Column("contract_category", "STRING", "permanent, fixed_term or apprentice"),
    ],
    "ref_employee_subgroups": [
        Column("employee_subgroup_code", "STRING", "PERSK code"),
        Column("employee_subgroup_label", "STRING", "Label"),
        Column("level_rank", "INT64", "1 staff, 2 supervisor, 3 manager"),
    ],
    "ref_action_types": [
        Column("action_type_code", "STRING", "MASSN code"),
        Column("action_type_label", "STRING", "Label"),
        Column("action_category", "STRING", "hire, rehire, org_change, contract_change or exit"),
    ],
    "ref_action_reasons": [
        Column("action_type_code", "STRING", "MASSN code"),
        Column("action_reason_code", "STRING", "MASSG code"),
        Column("action_reason_label", "STRING", "Label"),
        Column("exit_category", "STRING", "Exit category, exits only", required=False),
    ],
    "ref_absence_types": [
        Column("absence_type_code", "STRING", "AWART code"),
        Column("absence_type_label", "STRING", "Label"),
        Column("absence_category", "STRING", "leave, health, family, training or unjustified"),
        Column("counts_in_absenteeism", "BOOL", "Included in the absenteeism rate numerator"),
        Column("duration_unit", "STRING", "working_days or calendar_days"),
    ],
    "ref_public_holidays": [
        Column("holiday_date", "DATE", "Public holiday date"),
        Column("holiday_name", "STRING", "Holiday name"),
        Column("region_scope", "STRING", "FR-METRO (Alsace-Moselle excluded)"),
    ],
    "ref_calendar": [
        Column("calendar_date", "DATE", "Day"),
        Column("is_weekend", "BOOL", "Saturday or Sunday"),
        Column("is_public_holiday", "BOOL", "Metropolitan French public holiday"),
        Column("holiday_name", "STRING", "Holiday name", required=False),
        Column("is_working_day", "BOOL", "Monday to Friday and not a public holiday"),
    ],
}

TABLES = list(SCHEMAS)


def arrow_schema(table: str):
    import pyarrow as pa

    types = {
        "STRING": pa.string(), "DATE": pa.date32(), "INT64": pa.int64(), "FLOAT64": pa.float64(),
        "BOOL": pa.bool_(), "TIMESTAMP": pa.timestamp("us", tz="UTC"),
    }
    return pa.schema(
        [
            pa.field(c.name, types[c.type], nullable=not c.required, metadata={"description": c.description})
            for c in SCHEMAS[table] + META
        ]
    )
