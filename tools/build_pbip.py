"""Generate the Power BI project (PBIP, TMDL semantic model + PBIR report shell) in powerbi/.

Columns and types come from data/sample/manifest.json (written by export_samples.py from the
BigQuery mart schemas), so the model always matches the marts. Measures, relationships and the
RLS role are declared below. Run after export_samples.py; Power BI Desktop is needed only to
open, refresh and lay out the report.
"""

from __future__ import annotations

import json
import uuid

from common import PROJECT, ROOT

OUT = ROOT / "powerbi"
NAME = "PeopleAnalytics"
SEMANTIC = OUT / f"{NAME}.SemanticModel"
REPORT = OUT / f"{NAME}.Report"
SAMPLE_DIR_DEFAULT = str(ROOT / "data" / "sample")
NS = uuid.UUID("6f1c3a52-6f3e-4d3b-9a0e-2f6f0e9b7a11")

TABLES = [
    "dim_date", "dim_org_unit", "dim_employee", "dim_contract_type", "dim_level", "dim_absence_type",
    "dim_action_type", "sec_user_scope", "fct_headcount_monthly", "fct_movements", "fct_worktime_monthly",
    "fct_absence_monthly",
]
# rpt_kpi_monthly is deliberately NOT imported: it holds company-level aggregates that RLS could not
# restrict; reconciliation uses a DAX query (DAXQueries/) compared with docs/kpi-reconciliation.md.

TM_TYPES = {"STRING": "string", "INTEGER": "int64", "INT64": "int64", "FLOAT": "double", "FLOAT64": "double",
            "NUMERIC": "decimal", "BOOLEAN": "boolean", "BOOL": "boolean", "DATE": "dateTime"}
M_TYPES = {"string": "type text", "int64": "Int64.Type", "double": "type number", "decimal": "type number",
           "boolean": "type logical", "dateTime": "type date"}

KEYS = {"dim_date": "date", "dim_org_unit": "org_unit_id", "dim_employee": "employee_id",
        "dim_contract_type": "employee_group_code", "dim_level": "employee_subgroup_code",
        "dim_absence_type": "absence_type_code", "dim_action_type": "action_key"}
HIDDEN_TABLES = {"sec_user_scope"}
VISIBLE_FACT_COLUMNS = {"fct_movements": {"movement_type", "event_date"}, "fct_headcount_monthly": {"age_band"}}
SORT_BY = {("dim_date", "month_label"): "month_start", ("dim_date", "year_month"): "month_start",
           ("dim_date", "month_short_fr"): "month", ("fct_headcount_monthly", "age_band"): "age_band_order",
           ("dim_level", "level_label"): "level_rank"}
DISPLAY_NAMES = {}  # keep technical snake_case names: the report shows measure / column captions

RELATIONSHIPS = [
    ("fct_headcount_monthly", "month_start", "dim_date", "date"),
    ("fct_headcount_monthly", "org_unit_id", "dim_org_unit", "org_unit_id"),
    ("fct_headcount_monthly", "employee_id", "dim_employee", "employee_id"),
    ("fct_headcount_monthly", "employee_group_code", "dim_contract_type", "employee_group_code"),
    ("fct_headcount_monthly", "employee_subgroup_code", "dim_level", "employee_subgroup_code"),
    ("fct_movements", "month_start", "dim_date", "date"),
    ("fct_movements", "org_unit_id", "dim_org_unit", "org_unit_id"),
    ("fct_movements", "employee_id", "dim_employee", "employee_id"),
    ("fct_movements", "employee_group_code", "dim_contract_type", "employee_group_code"),
    ("fct_movements", "employee_subgroup_code", "dim_level", "employee_subgroup_code"),
    ("fct_movements", "action_key", "dim_action_type", "action_key"),
    ("fct_worktime_monthly", "month_start", "dim_date", "date"),
    ("fct_worktime_monthly", "org_unit_id", "dim_org_unit", "org_unit_id"),
    ("fct_worktime_monthly", "employee_id", "dim_employee", "employee_id"),
    ("fct_worktime_monthly", "employee_group_code", "dim_contract_type", "employee_group_code"),
    ("fct_absence_monthly", "month_start", "dim_date", "date"),
    ("fct_absence_monthly", "org_unit_id", "dim_org_unit", "org_unit_id"),
    ("fct_absence_monthly", "employee_id", "dim_employee", "employee_id"),
    ("fct_absence_monthly", "absence_type_code", "dim_absence_type", "absence_type_code"),
]

# Shared DAX fragments
END = "VAR _end = MAX ( dim_date[month_start] )"
WINDOW = END + "\nVAR _start = EDATE ( _end, -11 )"
IN_WINDOW = "REMOVEFILTERS ( dim_date ),\n        dim_date[month_start] >= _start,\n        dim_date[month_start] <= _end"
MONTHS_IN_WINDOW = ("VAR _months =\n    CALCULATE (\n        DISTINCTCOUNT ( dim_date[month_start] ),\n        "
                    + IN_WINDOW + "\n    )")

PCT = "0.0 %"
INT = "#,0"
DEC1 = "#,0.0"

# (table, name, folder, format, description, DAX)
MEASURES = [
    ("fct_headcount_monthly", "Headcount EoP", "Effectifs", INT,
     "Effectif fin de période : salariés actifs au dernier mois du contexte (semi-additif, jamais sommé dans le temps).",
     END + "\nRETURN\n    CALCULATE ( COUNTROWS ( fct_headcount_monthly ), dim_date[month_start] = _end )"),
    ("fct_headcount_monthly", "Headcount EoP (masked < 5)", "Effectifs", INT,
     "Effectif fin de période, masqué sous 5 personnes (répartition F/H par niveau).",
     "VAR _n = [Headcount EoP]\nRETURN\n    IF ( _n >= 5, _n )"),
    ("fct_headcount_monthly", "Headcount EoP Women", "Effectifs", INT,
     "Effectif fin de période, femmes (pyramide des âges).",
     "CALCULATE ( [Headcount EoP], dim_employee[gender_code] = \"2\" )"),
    ("fct_headcount_monthly", "Headcount EoP Men (negative)", "Effectifs", "#,0;#,0;0",
     "Effectif fin de période, hommes, en négatif pour la pyramide des âges (affiché en valeur absolue).",
     "- CALCULATE ( [Headcount EoP], dim_employee[gender_code] = \"1\" )"),
    ("fct_headcount_monthly", "FTE EoP", "Effectifs", DEC1,
     "ETP fin de période : somme des taux d'activité / 100 au dernier mois du contexte.",
     END + "\nRETURN\n    CALCULATE ( SUM ( fct_headcount_monthly[fte] ), dim_date[month_start] = _end )"),
    ("fct_headcount_monthly", "Headcount PY", "Effectifs", INT,
     "Effectif fin de période douze mois plus tôt.",
     "CALCULATE ( [Headcount EoP], DATEADD ( dim_date[date], -12, MONTH ) )"),
    ("fct_headcount_monthly", "Headcount Δ", "Effectifs", "+#,0;-#,0;0",
     "Variation de l'effectif sur douze mois.",
     "IF ( NOT ISBLANK ( [Headcount PY] ), [Headcount EoP] - [Headcount PY] )"),
    ("fct_headcount_monthly", "Avg Headcount 12M", "Effectifs", DEC1,
     "Effectif moyen sur 12 mois : moyenne des 12 effectifs de fin de mois (vide si moins de 12 mois d'historique).",
     WINDOW + "\n" + MONTHS_IN_WINDOW + "\nVAR _sum =\n    CALCULATE (\n        COUNTROWS ( fct_headcount_monthly ),\n        "
     + IN_WINDOW + "\n    )\nRETURN\n    IF ( _months = 12, DIVIDE ( _sum, 12 ) )"),
    ("fct_headcount_monthly", "Avg Headcount CDI 12M", "Effectifs", DEC1,
     "Effectif moyen CDI sur 12 mois : dénominateur du turnover CDI.",
     WINDOW + "\n" + MONTHS_IN_WINDOW + "\nVAR _sum =\n    CALCULATE (\n        COUNTROWS ( fct_headcount_monthly ),\n        "
     "dim_contract_type[contract_category] = \"permanent\",\n        " + IN_WINDOW
     + "\n    )\nRETURN\n    IF ( _months = 12, DIVIDE ( _sum, 12 ) )"),
    ("fct_headcount_monthly", "Avg Tenure (years)", "Effectifs", DEC1,
     "Ancienneté moyenne au dernier mois du contexte (depuis l'entrée du parcours en cours).",
     END + "\nRETURN\n    CALCULATE ( AVERAGE ( fct_headcount_monthly[tenure_years] ), dim_date[month_start] = _end )"),
    ("fct_headcount_monthly", "Avg Age", "Effectifs", DEC1,
     "Âge moyen au dernier mois du contexte.",
     END + "\nRETURN\n    CALCULATE ( AVERAGE ( fct_headcount_monthly[age_years] ), dim_date[month_start] = _end )"),
    ("fct_headcount_monthly", "Female Share %", "Effectifs", PCT,
     "Part des femmes dans l'effectif fin de période.",
     "DIVIDE ( CALCULATE ( [Headcount EoP], dim_employee[gender_code] = \"2\" ), [Headcount EoP] )"),

    ("fct_movements", "Hires", "Mouvements", INT, "Entrées : embauches et réintégrations.",
     "CALCULATE ( COUNTROWS ( fct_movements ), fct_movements[is_entry] = TRUE () )"),
    ("fct_movements", "Exits", "Mouvements", INT, "Sorties, datées du dernier jour travaillé.",
     "CALCULATE ( COUNTROWS ( fct_movements ), fct_movements[is_exit] = TRUE () )"),
    ("fct_movements", "Exits CDI", "Mouvements", INT, "Sorties de salariés en CDI, toutes causes.",
     "CALCULATE ( COUNTROWS ( fct_movements ), fct_movements[is_cdi_exit] = TRUE () )"),
    ("fct_movements", "Resignations CDI", "Mouvements", INT, "Démissions de salariés en CDI.",
     "CALCULATE ( COUNTROWS ( fct_movements ), fct_movements[is_cdi_exit] = TRUE (), fct_movements[is_resignation] = TRUE () )"),
    ("fct_movements", "Turnover CDI 12M %", "Mouvements", PCT,
     "Indicateur principal : sorties de CDI toutes causes sur 12 mois / effectif moyen CDI sur 12 mois. Fins de CDD exclues.",
     WINDOW + "\nVAR _exits =\n    CALCULATE ( [Exits CDI], " + IN_WINDOW.replace("\n        ", " ") + " )\nRETURN\n    DIVIDE ( _exits, [Avg Headcount CDI 12M] )"),
    ("fct_movements", "Resignation Rate 12M %", "Mouvements", PCT,
     "Démissions de CDI sur 12 mois / effectif moyen CDI sur 12 mois.",
     WINDOW + "\nVAR _n =\n    CALCULATE ( [Resignations CDI], " + IN_WINDOW.replace("\n        ", " ") + " )\nRETURN\n    DIVIDE ( _n, [Avg Headcount CDI 12M] )"),
    ("fct_movements", "Total Exit Rate 12M %", "Mouvements", PCT,
     "Toutes sorties sur 12 mois, CDD et alternants compris / effectif moyen sur 12 mois. Ne pas comparer au turnover CDI.",
     WINDOW + "\nVAR _n =\n    CALCULATE ( [Exits], " + IN_WINDOW.replace("\n        ", " ") + " )\nRETURN\n    DIVIDE ( _n, [Avg Headcount 12M] )"),

    ("fct_worktime_monthly", "Theoretical Hours", "Absences", INT,
     "Heures théoriques : jours ouvrés (fériés de métropole exclus) x WOSTD / 5.",
     "SUM ( fct_worktime_monthly[theoretical_hours] )"),
    ("fct_absence_monthly", "Absence Hours (counted)", "Absences", INT,
     "Heures d'absence des types de l'absentéisme (maladie, accident du travail, accident de trajet, maladie professionnelle, absence injustifiée).",
     "CALCULATE ( SUM ( fct_absence_monthly[absence_hours] ), dim_absence_type[counts_in_absenteeism] = TRUE () )"),
    ("fct_absence_monthly", "Absence Hours (all incl. leave)", "Absences", INT,
     "Heures d'absence de tous les types, congés payés et RTT inclus.",
     "SUM ( fct_absence_monthly[absence_hours] )"),
    ("fct_absence_monthly", "Absenteeism %", "Absences", PCT,
     "Taux d'absentéisme : heures des types comptés / heures théoriques. Congés payés, RTT, maternité, paternité et formation exclus.",
     "DIVIDE ( [Absence Hours (counted)], [Theoretical Hours] )"),
    ("fct_absence_monthly", "Total Absence incl. Leave %", "Absences", PCT,
     "Absences totales, congés inclus : heures de tous les types / heures théoriques. Indicateur de disponibilité, jamais présenté comme de l'absentéisme.",
     "DIVIDE ( [Absence Hours (all incl. leave)], [Theoretical Hours] )"),
    ("fct_absence_monthly", "Absenteeism 12M %", "Absences", PCT,
     "Taux d'absentéisme sur les 12 mois glissants se terminant au dernier mois du contexte.",
     WINDOW + "\n" + MONTHS_IN_WINDOW + "\nVAR _num = CALCULATE ( [Absence Hours (counted)], " + IN_WINDOW.replace("\n        ", " ")
     + " )\nVAR _den = CALCULATE ( [Theoretical Hours], " + IN_WINDOW.replace("\n        ", " ")
     + " )\nRETURN\n    IF ( _months = 12, DIVIDE ( _num, _den ) )"),
    ("fct_absence_monthly", "Total Absence incl. Leave 12M %", "Absences", PCT,
     "Absences totales, congés inclus, sur 12 mois glissants.",
     WINDOW + "\n" + MONTHS_IN_WINDOW + "\nVAR _num = CALCULATE ( [Absence Hours (all incl. leave)], " + IN_WINDOW.replace("\n        ", " ")
     + " )\nVAR _den = CALCULATE ( [Theoretical Hours], " + IN_WINDOW.replace("\n        ", " ")
     + " )\nRETURN\n    IF ( _months = 12, DIVIDE ( _num, _den ) )"),
]

SCOPE_VARS = """VAR _upn = LOWER ( USERPRINCIPALNAME () )
VAR _scope = FILTER ( sec_user_scope, sec_user_scope[user_upn] = _upn )
VAR _all = NOT ISEMPTY ( FILTER ( _scope, sec_user_scope[scope_type] = "ALL" ) )"""

RLS = {
    "sec_user_scope": "sec_user_scope[user_upn] = LOWER ( USERPRINCIPALNAME () )",
    "dim_org_unit": SCOPE_VARS + """
VAR _sites = SELECTCOLUMNS ( FILTER ( _scope, sec_user_scope[scope_type] = "SITE" ), "v", sec_user_scope[scope_value] )
VAR _depts = SELECTCOLUMNS ( FILTER ( _scope, sec_user_scope[scope_type] = "DEPT" ), "v", sec_user_scope[scope_value] )
RETURN
    _all
        || dim_org_unit[site_code] IN _sites
        || dim_org_unit[org_unit_id] IN _depts""",
    "dim_employee": SCOPE_VARS + """
RETURN
    _all
        || NOT ISEMPTY (
            FILTER (
                _scope,
                sec_user_scope[scope_type] = "SITE"
                    && CONTAINSSTRING ( dim_employee[site_codes_history], "|" & sec_user_scope[scope_value] & "|" )
            )
        )
        || NOT ISEMPTY (
            FILTER (
                _scope,
                sec_user_scope[scope_type] = "DEPT"
                    && CONTAINSSTRING ( dim_employee[org_unit_ids_history], "|" & sec_user_scope[scope_value] & "|" )
            )
        )""",
}


def tag(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


def q(name: str) -> str:
    return f"'{name}'" if any(c in name for c in " .=:'()%<Δ") else name


def indent(text: str, level: int) -> str:
    pad = "\t" * level
    return "\n".join(pad + line if line.strip() else "" for line in text.splitlines())


def desc(text: str, level: int) -> str:
    return "\n".join("\t" * level + "/// " + line for line in [text] if text) + ("\n" if text else "")


def table_tmdl(name: str, spec: dict) -> str:
    columns = spec["columns"]
    descriptions = spec.get("descriptions", {})
    is_fact = name.startswith("fct_")
    lines = [desc(spec.get("table_description", ""), 0) + f"table {name}"]
    if name in HIDDEN_TABLES:
        lines.append("\tisHidden")
    if name == "dim_date":
        lines.append("\tdataCategory: Time")
    lines.append(f"\tlineageTag: {tag(name)}")
    lines.append("")

    for table, mname, folder, fmt, text, dax in MEASURES:
        if table != name:
            continue
        lines.append(desc(text, 1) + f"\tmeasure {q(mname)} =")
        lines.append(indent(dax, 3))
        lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {tag(name, 'measure', mname)}")
        lines.append("")

    for col, bq_type in columns.items():
        dtype = TM_TYPES[bq_type]
        lines.append(desc(descriptions.get(col, ""), 1) + f"\tcolumn {col}")
        lines.append(f"\t\tdataType: {dtype}")
        if dtype == "dateTime":
            lines.append("\t\tformatString: yyyy-mm-dd")
        elif dtype == "double" and not is_fact:
            lines.append("\t\tformatString: #,0.00")
        if KEYS.get(name) == col:
            lines.append("\t\tisKey")
        hidden = (is_fact and col not in VISIBLE_FACT_COLUMNS.get(name, set())) or col.endswith("_history") \
            or col.endswith("_order") or (name, col) in {("dim_date", "month")}
        if hidden or name in HIDDEN_TABLES:
            lines.append("\t\tisHidden")
        lines.append(f"\t\tlineageTag: {tag(name, col)}")
        lines.append("\t\tsummarizeBy: none")
        lines.append(f"\t\tsourceColumn: {col}")
        if (name, col) in SORT_BY:
            lines.append(f"\t\tsortByColumn: {SORT_BY[(name, col)]}")
        lines.append("")
        lines.append("\t\tannotation SummarizationSetBy = User")
        lines.append("")

    typed = ", ".join(f'{{"{c}", {M_TYPES[TM_TYPES[t]]}}}' for c, t in columns.items())
    lines.append(f"\tpartition {name} = m")
    lines.append("\t\tmode: import")
    lines.append("\t\tsource =")
    lines.append(indent(f'let\n    Source = LoadMart("{name}"),\n    Typed = Table.TransformColumnTypes(Source, {{{typed}}}, "en-US")\nin\n    Typed', 3))
    lines.append("")
    lines.append("\tannotation PBI_ResultType = Table")
    lines.append("")
    return "\n".join(lines)


def expressions_tmdl() -> str:
    load_mart = """(tableName as text) as table =>
let
    Source =
        if DataSource = "BigQuery" then
            GoogleBigQuery.Database([BillingProject = BigQueryProject]){[Name = BigQueryProject]}[Data]{[Name = BigQueryDataset, Kind = "Schema"]}[Data]{[Name = tableName, Kind = "Table"]}[Data]
        else
            let
                Csv = Csv.Document(File.Contents(SampleFolder & "\\" & tableName & ".csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
                Promoted = Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),
                Nulls = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, Table.ColumnNames(Promoted))
            in
                Nulls
in
    Source"""
    params = [
        ("DataSource", '"Local" meta [IsParameterQuery = true, List = {"Local", "BigQuery"}, DefaultValue = "Local", Type = "Text", IsParameterQueryRequired = true]',
         "Source des données : Local (CSV de data/sample, par défaut) ou BigQuery (démonstration en direct)."),
        ("SampleFolder", f'"{SAMPLE_DIR_DEFAULT}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
         "Chemin absolu du dossier data/sample du dépôt cloné (à adapter sur un autre poste)."),
        ("BigQueryProject", f'"{PROJECT}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
         "Projet GCP (BillingProject du connecteur)."),
        ("BigQueryDataset", '"hr_marts" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
         "Dataset des marts."),
    ]
    out = []
    for name, value, text in params:
        out.append(desc(text, 0) + f"expression {name} = {value}")
        out.append(f"\tlineageTag: {tag('expr', name)}")
        out.append("")
        out.append("\tannotation PBI_ResultType = Text")
        out.append("")
    out.append(desc("Charge une table des marts depuis BigQuery ou depuis les CSV, selon DataSource.", 0) + "expression LoadMart =")
    out.append(indent(load_mart, 2))
    out.append(f"\tlineageTag: {tag('expr', 'LoadMart')}")
    out.append("")
    out.append("\tannotation PBI_ResultType = Function")
    out.append("")
    return "\n".join(out)


def relationships_tmdl() -> str:
    out = []
    for from_t, from_c, to_t, to_c in RELATIONSHIPS:
        out.append(f"relationship {tag('rel', from_t, from_c, to_t)}")
        out.append(f"\tfromColumn: {from_t}.{from_c}")
        out.append(f"\ttoColumn: {to_t}.{to_c}")
        out.append("")
    return "\n".join(out)


def role_tmdl() -> str:
    out = ["/// Périmètre dynamique : DRH tout, directeur de site son site, manager son ou ses départements.",
           "/// Table sec_user_scope ; testé dans Power BI Desktop avec « Afficher en tant que ».",
           "role dynamic_scope", "\tmodelPermission: read", ""]
    for table, dax in RLS.items():
        out.append(f"\ttablePermission {table} =")
        out.append(indent(dax, 3))
        out.append("")
    out.append(f"\tannotation PBI_Id = {tag('role').replace('-', '')}")
    out.append("")
    return "\n".join(out)


def model_tmdl() -> str:
    lines = ["model Model", "\tculture: fr-FR", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: fr-FR", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             'annotation PBI_QueryOrder = ' + json.dumps(["DataSource", "SampleFolder", "BigQueryProject", "BigQueryDataset",
                                                          "LoadMart", *TABLES]), ""]
    lines += [f"ref table {t}" for t in TABLES]
    lines += ["", "ref role dynamic_scope", ""]
    return "\n".join(lines)


def reconciliation_dax() -> str:
    return """// Réconciliation DAX vs SQL (rpt_kpi_monthly) : exécuter dans la vue Requête DAX de Power BI Desktop,
// sans rôle actif, et comparer avec docs/kpi-reconciliation.md.
EVALUATE
VAR _months = { DATE ( 2025, 9, 1 ), DATE ( 2026, 3, 1 ), DATE ( 2026, 9, 1 ) }
RETURN
    ADDCOLUMNS (
        SELECTCOLUMNS ( _months, "month_start", [Value] ),
        "headcount", CALCULATE ( [Headcount EoP], dim_date[month_start] = [month_start] ),
        "fte", CALCULATE ( [FTE EoP], dim_date[month_start] = [month_start] ),
        "hires", CALCULATE ( [Hires], dim_date[month_start] = [month_start] ),
        "exits", CALCULATE ( [Exits], dim_date[month_start] = [month_start] ),
        "cdi_turnover_12m", CALCULATE ( [Turnover CDI 12M %], dim_date[month_start] = [month_start] ),
        "resignation_rate_12m", CALCULATE ( [Resignation Rate 12M %], dim_date[month_start] = [month_start] ),
        "total_exit_rate_12m", CALCULATE ( [Total Exit Rate 12M %], dim_date[month_start] = [month_start] ),
        "absenteeism_rate", CALCULATE ( [Absenteeism %], dim_date[month_start] = [month_start] ),
        "total_absence_rate", CALCULATE ( [Total Absence incl. Leave %], dim_date[month_start] = [month_start] ),
        "absenteeism_rate_12m", CALCULATE ( [Absenteeism 12M %], dim_date[month_start] = [month_start] ),
        "female_share", CALCULATE ( [Female Share %], dim_date[month_start] = [month_start] ),
        "avg_tenure_years", CALCULATE ( [Avg Tenure (years)], dim_date[month_start] = [month_start] ),
        "avg_age_years", CALCULATE ( [Avg Age], dim_date[month_start] = [month_start] )
    )
ORDER BY [month_start]
"""


PAGES = [("overview", "Vue globale"), ("absenteeism", "Absentéisme"), ("movements", "Mouvements"),
         ("workforce", "Effectifs détaillés")]


def write(path, text: str, crlf: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\r\n" if crlf else "\n")


def write_json(path, data) -> None:
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    manifest = json.loads((ROOT / "data" / "sample" / "manifest.json").read_text(encoding="utf-8"))
    definition = SEMANTIC / "definition"
    write(definition / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    write(definition / "model.tmdl", model_tmdl())
    write(definition / "expressions.tmdl", expressions_tmdl())
    write(definition / "relationships.tmdl", relationships_tmdl())
    write(definition / "roles" / "dynamic_scope.tmdl", role_tmdl())
    for name in TABLES:
        write(definition / "tables" / f"{name}.tmdl", table_tmdl(name, manifest[name]))
    write(SEMANTIC / "DAXQueries" / "Reconciliation.dax", reconciliation_dax())
    write_json(SEMANTIC / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})

    write_json(REPORT / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    rdef = REPORT / "definition"
    write_json(rdef / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    write_json(rdef / "report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {"baseTheme": {
            "name": "CY24SU06", "type": "SharedResources",
            "reportVersionAtImport": {"visual": "2.0.0", "page": "2.0.0", "report": "3.0.0"}}}})
    write_json(rdef / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p for p, _ in PAGES], "activePageName": PAGES[0][0]})
    for page, label in PAGES:
        write_json(rdef / "pages" / page / "page.json", {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": page, "displayName": label, "displayOption": "FitToPage", "height": 720, "width": 1280})

    write_json(OUT / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
    print(f"PBIP written to {OUT}: {len(TABLES)} tables, {len(MEASURES)} measures, {len(RELATIONSHIPS)} relationships")


if __name__ == "__main__":
    main()
