"""Organisation and code lists defined by this project.

The codes are *not* SAP standard customizing: SAP action types, absence types
and employee groups are configured per customer, so the project defines its own.
"""

from __future__ import annotations

from dataclasses import dataclass

COMPANY_CODE = "FR01"  # BUKRS
PERSONNEL_SUBAREA = "0001"  # BTRTL
LEAVER_POSITION = "99999999"  # PLANS after an exit
FULL_TIME_WEEKLY_HOURS = 35.0
ROOT_ORG_UNIT = "50000000"


@dataclass(frozen=True)
class Site:
    code: str  # WERKS
    index: int
    name: str

    @property
    def org_unit_id(self) -> str:
        return f"50{self.index}00000"


SITES = [
    Site("S100", 1, "Site Nord"),
    Site("S200", 2, "Site Est"),
    Site("S300", 3, "Site Ouest"),
    Site("S400", 4, "Siège"),
]
SITE_BY_CODE = {s.code: s for s in SITES}


@dataclass(frozen=True)
class Department:
    number: int
    name: str
    site_code: str
    size: int  # target headcount (excluding seasonal staff)
    cdi_exit_rate: float  # annual CDI exit probability, retirement excluded
    female_share: float
    manager_share: float  # PERSK "CA"
    supervisor_share: float  # PERSK "AM"
    part_time_rate: float
    cdd_share: float  # share of hires on fixed-term contracts
    apprentice_share: float
    work_accident_risk: float  # multiplier for work accidents / occupational disease
    growth_per_year: float = 0.0
    seasonal: bool = False  # summer seasonal fixed-term hires

    @property
    def code(self) -> str:
        return f"D{self.number:02d}"

    @property
    def site(self) -> Site:
        return SITE_BY_CODE[self.site_code]

    @property
    def org_unit_id(self) -> str:
        return f"50{self.site.index}{self.number:05d}"

    @property
    def cost_center(self) -> str:  # KOSTL
        return f"10{self.site.index}{self.number:02d}0"


DEPARTMENTS = [
    Department(1, "Fabrication", "S100", 150, 0.105, 0.25, 0.06, 0.18, 0.06, 0.55, 0.06, 3.0, seasonal=True),
    Department(2, "Maintenance", "S100", 40, 0.075, 0.08, 0.10, 0.25, 0.04, 0.20, 0.10, 2.5),
    Department(3, "Logistique", "S100", 85, 0.135, 0.20, 0.06, 0.18, 0.08, 0.55, 0.06, 2.5, seasonal=True),
    Department(4, "Assemblage", "S200", 140, 0.105, 0.30, 0.06, 0.18, 0.07, 0.50, 0.06, 2.5, seasonal=True),
    Department(5, "Qualité", "S200", 35, 0.085, 0.55, 0.25, 0.30, 0.10, 0.20, 0.10, 1.0),
    Department(6, "Service client", "S200", 70, 0.150, 0.70, 0.08, 0.20, 0.25, 0.45, 0.08, 0.5),
    Department(7, "Commercial", "S300", 80, 0.130, 0.45, 0.35, 0.25, 0.08, 0.20, 0.15, 0.5),
    Department(8, "Achats", "S300", 25, 0.080, 0.50, 0.40, 0.30, 0.10, 0.15, 0.10, 0.3),
    Department(9, "Recherche et développement", "S300", 65, 0.070, 0.35, 0.70, 0.15, 0.08, 0.15, 0.15, 0.3, 0.03),
    Department(10, "Finance", "S400", 35, 0.080, 0.60, 0.45, 0.30, 0.18, 0.15, 0.12, 0.3),
    Department(11, "Ressources humaines", "S400", 30, 0.090, 0.80, 0.40, 0.30, 0.25, 0.15, 0.15, 0.3),
    Department(12, "Informatique", "S400", 45, 0.115, 0.25, 0.65, 0.15, 0.08, 0.15, 0.15, 0.3, 0.03),
]
DEPT_BY_CODE = {d.code: d for d in DEPARTMENTS}

# Employee groups (PERSG) and subgroups (PERSK)
PERSG_CDI, PERSG_CDD, PERSG_APPRENTICE = "1", "2", "3"
EMPLOYEE_GROUPS = [
    (PERSG_CDI, "CDI", "permanent"),
    (PERSG_CDD, "CDD", "fixed_term"),
    (PERSG_APPRENTICE, "Alternant", "apprentice"),
]
PERSK_MANAGER, PERSK_SUPERVISOR, PERSK_STAFF = "CA", "AM", "EO"
EMPLOYEE_SUBGROUPS = [
    (PERSK_MANAGER, "Cadre", 3),
    (PERSK_SUPERVISOR, "Agent de maîtrise", 2),
    (PERSK_STAFF, "Employé / ouvrier", 1),
]
LEVEL_RANK = {code: rank for code, _, rank in EMPLOYEE_SUBGROUPS}

# Personnel actions (MASSN) and reasons (MASSG)
MASSN_HIRE, MASSN_REHIRE, MASSN_ORG_CHANGE, MASSN_CONTRACT_CHANGE, MASSN_EXIT = "H1", "H2", "O1", "C1", "X1"
ACTION_TYPES = [
    (MASSN_HIRE, "Embauche", "hire"),
    (MASSN_REHIRE, "Réintégration", "rehire"),
    (MASSN_ORG_CHANGE, "Changement d'affectation", "org_change"),
    (MASSN_CONTRACT_CHANGE, "Changement de contrat", "contract_change"),
    (MASSN_EXIT, "Sortie", "exit"),
]
# (MASSN, MASSG, label, exit_category)
ACTION_REASONS = [
    (MASSN_HIRE, "01", "Remplacement", None),
    (MASSN_HIRE, "02", "Création de poste", None),
    (MASSN_HIRE, "03", "Renfort saisonnier", None),
    (MASSN_REHIRE, "01", "Retour d'un ancien salarié", None),
    (MASSN_ORG_CHANGE, "01", "Mutation", None),
    (MASSN_ORG_CHANGE, "02", "Promotion", None),
    (MASSN_CONTRACT_CHANGE, "01", "Transformation CDD en CDI", None),
    (MASSN_CONTRACT_CHANGE, "02", "Embauche en CDI après alternance", None),
    (MASSN_EXIT, "01", "Démission", "resignation"),
    (MASSN_EXIT, "02", "Licenciement", "dismissal"),
    (MASSN_EXIT, "03", "Rupture conventionnelle", "mutual_agreement"),
    (MASSN_EXIT, "04", "Fin de CDD", "contract_end"),
    (MASSN_EXIT, "05", "Fin de contrat d'alternance", "contract_end"),
    (MASSN_EXIT, "06", "Départ à la retraite", "retirement"),
]
EXIT_RESIGNATION, EXIT_DISMISSAL, EXIT_MUTUAL, EXIT_CDD_END, EXIT_APPRENTICE_END, EXIT_RETIREMENT = (
    "01", "02", "03", "04", "05", "06",
)


@dataclass(frozen=True)
class AbsenceType:
    code: str  # AWART
    label: str
    category: str
    counts_in_absenteeism: bool
    duration_unit: str  # "working_days" or "calendar_days"
    priority: int  # tie-break when two absences start the same day (lower wins)


AB_PAID_LEAVE, AB_RTT, AB_SICKNESS, AB_WORK_ACCIDENT, AB_COMMUTING_ACCIDENT = "0100", "0110", "0200", "0210", "0220"
AB_OCCUPATIONAL_DISEASE, AB_MATERNITY, AB_PATERNITY, AB_TRAINING, AB_UNJUSTIFIED = "0230", "0300", "0310", "0400", "0500"

ABSENCE_TYPES = [
    AbsenceType(AB_PAID_LEAVE, "Congés payés", "leave", False, "working_days", 8),
    AbsenceType(AB_RTT, "RTT", "leave", False, "working_days", 9),
    AbsenceType(AB_SICKNESS, "Maladie", "health", True, "working_days", 4),
    AbsenceType(AB_WORK_ACCIDENT, "Accident du travail", "health", True, "working_days", 2),
    AbsenceType(AB_COMMUTING_ACCIDENT, "Accident de trajet", "health", True, "working_days", 3),
    AbsenceType(AB_OCCUPATIONAL_DISEASE, "Maladie professionnelle", "health", True, "working_days", 1),
    AbsenceType(AB_MATERNITY, "Congé maternité", "family", False, "calendar_days", 0),
    AbsenceType(AB_PATERNITY, "Congé paternité", "family", False, "calendar_days", 0),
    AbsenceType(AB_TRAINING, "Formation", "training", False, "working_days", 6),
    AbsenceType(AB_UNJUSTIFIED, "Absence injustifiée", "unjustified", True, "working_days", 5),
]
ABSENCE_BY_CODE = {a.code: a for a in ABSENCE_TYPES}

WORK_SCHEDULES = {100: "NORM", 90: "TP90", 80: "TP80", 50: "TP50"}  # EMPCT -> SCHKZ

NATIONALITIES = [("FR", 0.93), ("PT", 0.015), ("ES", 0.012), ("IT", 0.01), ("BE", 0.008), ("MA", 0.012), ("DE", 0.005), ("PL", 0.008)]


def reference_tables() -> dict[str, list[dict]]:
    return {
        "ref_sites": [
            {"site_code": s.code, "site_name": s.name, "site_org_unit_id": s.org_unit_id} for s in SITES
        ],
        "ref_employee_groups": [
            {"employee_group_code": c, "employee_group_label": l, "contract_category": k} for c, l, k in EMPLOYEE_GROUPS
        ],
        "ref_employee_subgroups": [
            {"employee_subgroup_code": c, "employee_subgroup_label": l, "level_rank": r} for c, l, r in EMPLOYEE_SUBGROUPS
        ],
        "ref_action_types": [
            {"action_type_code": c, "action_type_label": l, "action_category": k} for c, l, k in ACTION_TYPES
        ],
        "ref_action_reasons": [
            {"action_type_code": t, "action_reason_code": r, "action_reason_label": l, "exit_category": e}
            for t, r, l, e in ACTION_REASONS
        ],
        "ref_absence_types": [
            {
                "absence_type_code": a.code,
                "absence_type_label": a.label,
                "absence_category": a.category,
                "counts_in_absenteeism": a.counts_in_absenteeism,
                "duration_unit": a.duration_unit,
            }
            for a in ABSENCE_TYPES
        ],
    }
