"""Month-by-month workforce simulation producing per-employee event histories.

The simulation always runs whole months, in chronological order, with a single
seeded RNG. Running it to a later as-of date therefore replays exactly the same
past and only appends new months (needed to demonstrate incremental models).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from hr_generator import reference as ref
from hr_generator.config import GeneratorConfig
from hr_generator.work_calendar import WorkCalendar, add_months, month_end

RETIREMENT_MIN_AGE = 62
RETIREMENT_MAX_AGE = 67
RETIREMENT_ANNUAL_PROB = 0.35
TRANSFER_MONTHLY_PROB = 0.001
PROMOTION_MONTHLY_PROB = {ref.PERSK_STAFF: 0.003, ref.PERSK_SUPERVISOR: 0.0015}
WORKTIME_CHANGE_MONTHLY_PROB = 0.002
REHIRE_PROB = 0.03
SEASONAL_HIRE_SHARE = 0.04
STAFFING_BUFFER = 1.025  # hiring target above headcount target, offsets the 1-3 month replacement delay
CONVERSION_PROB = {"cdd": 0.30, "apprentice": 0.25, "seasonal": 0.05}
CDI_EXIT_REASONS = [(ref.EXIT_RESIGNATION, 0.60), (ref.EXIT_MUTUAL, 0.20), (ref.EXIT_DISMISSAL, 0.20)]
PART_TIME_LEVELS = [(80, 0.5), (90, 0.3), (50, 0.2)]


@dataclass(frozen=True)
class State:
    dept: str
    persg: str
    persk: str
    empct: int
    position: str


@dataclass(frozen=True)
class Event:
    begda: date  # first day of the resulting infotype records
    kind: str  # hire | rehire | org_change | contract_change | exit | worktime
    state: State
    massn: str | None = None
    massg: str | None = None

    @property
    def effective_date(self) -> date:
        """Date the event is known to have happened: the last worked day for an exit."""
        return self.begda - timedelta(days=1) if self.kind == "exit" else self.begda


@dataclass
class Employee:
    pernr: str
    gender: str  # GESCH: "1" male, "2" female
    birth_date: date
    nationality: str
    events: list[Event] = field(default_factory=list)
    state: State | None = None
    active: bool = False
    contract_end: date | None = None
    seasonal: bool = False
    hired_on: date | None = None

    @property
    def last_begda(self) -> date:
        return self.events[-1].begda

    def age_on(self, d: date) -> int:
        return d.year - self.birth_date.year - ((d.month, d.day) < (self.birth_date.month, self.birth_date.day))


def _monthly(annual: float) -> float:
    return 1.0 - (1.0 - annual) ** (1.0 / 12.0)


def _weighted(rng: random.Random, pairs):
    values, weights = zip(*pairs)
    return rng.choices(values, weights=weights)[0]


class PopulationSimulator:
    def __init__(self, config: GeneratorConfig, calendar: WorkCalendar):
        self.config = config
        self.cal = calendar
        self.rng = random.Random(f"{config.seed}|population")
        self.employees: dict[str, Employee] = {}
        self.active: dict[str, Employee] = {}
        self.pending: dict[int, list[tuple[str, str]]] = {}  # month index -> [(dept, MASSG)]
        self.created_positions = {d.code: 0 for d in ref.DEPARTMENTS}
        self.former: list[tuple[str, date, str]] = []  # (pernr, exit date, dept) of rehire candidates
        self._next_pernr = 10000001
        self._next_position = 30000001

    # --- identifiers -------------------------------------------------------
    def _new_pernr(self) -> str:
        pernr = f"{self._next_pernr:08d}"
        self._next_pernr += 1
        return pernr

    def _new_position(self) -> str:
        pos = f"{self._next_position:08d}"
        self._next_position += 1
        return pos

    # --- attribute draws ---------------------------------------------------
    def _draw_gender(self, dept: ref.Department) -> str:
        return "2" if self.rng.random() < dept.female_share else "1"

    def _draw_level(self, dept: ref.Department, gender: str, persg: str) -> str:
        if persg == ref.PERSG_APPRENTICE:
            return ref.PERSK_STAFF
        manager = dept.manager_share * (0.8 if gender == "2" else 1.15) * (0.3 if persg == ref.PERSG_CDD else 1.0)
        u = self.rng.random()
        if u < manager:
            return ref.PERSK_MANAGER
        if u < manager + dept.supervisor_share:
            return ref.PERSK_SUPERVISOR
        return ref.PERSK_STAFF

    def _draw_empct(self, dept: ref.Department, gender: str, persg: str) -> int:
        if persg == ref.PERSG_APPRENTICE:
            return 100
        p = dept.part_time_rate * (1.4 if gender == "2" else 0.45)
        return _weighted(self.rng, PART_TIME_LEVELS) if self.rng.random() < p else 100

    def _draw_contract(self, dept: ref.Department) -> str:
        u = self.rng.random()
        if u < dept.apprentice_share:
            return ref.PERSG_APPRENTICE
        if u < dept.apprentice_share + dept.cdd_share:
            return ref.PERSG_CDD
        return ref.PERSG_CDI

    def _draw_age_at_hire(self, persg: str) -> float:
        if persg == ref.PERSG_APPRENTICE:
            return self.rng.uniform(18.0, 25.9)
        if persg == ref.PERSG_CDD:
            return self.rng.triangular(19.0, 55.0, 25.0)
        return self.rng.triangular(21.0, 58.0, 30.0)

    def _draw_contract_end(self, persg: str, start: date) -> date | None:
        if persg == ref.PERSG_CDD:
            return start + timedelta(days=self.rng.randint(180, 540))
        if persg == ref.PERSG_APPRENTICE:
            return start + timedelta(days=self.rng.randint(365, 1095))
        return None

    def _new_employee(self, dept: ref.Department, birth_date: date, gender: str) -> Employee:
        nationality = _weighted(self.rng, ref.NATIONALITIES)
        emp = Employee(self._new_pernr(), gender, birth_date, nationality)
        self.employees[emp.pernr] = emp
        return emp

    # --- events ------------------------------------------------------------
    def _add(self, emp: Employee, event: Event) -> bool:
        if emp.events and event.begda <= emp.last_begda:
            return False  # one record start per day at most
        emp.events.append(event)
        emp.state = event.state
        return True

    def _start(self, emp: Employee, hire: date, persg: str, kind: str, massn: str, massg: str,
               dept: ref.Department, persk: str, empct: int, seasonal: bool = False,
               contract_end: date | None = None) -> None:
        state = State(dept.code, persg, persk, empct, self._new_position())
        if self._add(emp, Event(hire, kind, state, massn, massg)):
            emp.active = True
            emp.hired_on = hire
            emp.seasonal = seasonal
            emp.contract_end = contract_end if contract_end is not None else self._draw_contract_end(persg, hire)
            self.active[emp.pernr] = emp

    def _exit(self, emp: Employee, last_day: date, reason: str) -> None:
        state = replace(emp.state, position=ref.LEAVER_POSITION)
        if not self._add(emp, Event(last_day + timedelta(days=1), "exit", state, ref.MASSN_EXIT, reason)):
            return
        emp.active = False
        emp.contract_end = None
        self.active.pop(emp.pernr, None)
        if reason in (ref.EXIT_RESIGNATION, ref.EXIT_MUTUAL) and emp.state.persg == ref.PERSG_CDI:
            self.former.append((emp.pernr, last_day, emp.state.dept))

    # --- initial stock -----------------------------------------------------
    def _create_stock(self) -> None:
        start = self.config.history_start
        for dept in ref.DEPARTMENTS:
            for _ in range(dept.size):
                u = self.rng.random()
                persg = ref.PERSG_APPRENTICE if u < 0.04 else ref.PERSG_CDD if u < 0.12 else ref.PERSG_CDI
                if persg == ref.PERSG_APPRENTICE:
                    age = self.rng.uniform(18.5, 25.9)
                    tenure = self.rng.uniform(0.05, min(2.0, age - 18.0))
                    contract_end = start + timedelta(days=self.rng.randint(30, 700))
                elif persg == ref.PERSG_CDD:
                    age = self.rng.triangular(19.0, 55.0, 26.0)
                    tenure = self.rng.uniform(0.05, 0.9)
                    contract_end = start + timedelta(days=self.rng.randint(15, 365))
                else:
                    age = self.rng.triangular(20.0, 64.0, 43.0)
                    tenure = max(0.1, min(age - 19.0, self.rng.expovariate(1 / 9.0), 30.0))
                    contract_end = None
                gender = self._draw_gender(dept)
                persk = self._draw_level(dept, gender, persg)
                empct = self._draw_empct(dept, gender, persg)
                birth = start - timedelta(days=int(age * 365.25))
                raw_hire = start - timedelta(days=max(1, int(tenure * 365.25)))
                hire = date(raw_hire.year, raw_hire.month, 1)
                emp = self._new_employee(dept, birth, gender)
                self._start(emp, hire, persg, "hire", ref.MASSN_HIRE, "01", dept, persk, empct,
                            contract_end=contract_end)

    # --- monthly steps -----------------------------------------------------
    def _hire(self, dept: ref.Department, massg: str, year: int, month: int) -> None:
        days = self.cal.working_days_in_month(year, month)
        hire = days[0] if self.rng.random() < 0.5 else self.rng.choice(days)
        if massg != "03" and self.rng.random() < REHIRE_PROB:
            candidates = [
                (p, d) for p, d, dep in self.former
                if dep == dept.code and d <= hire - timedelta(days=180)
                and not self.employees[p].active and self.employees[p].age_on(hire) < 60
            ]
            if candidates:
                pernr, _ = self.rng.choice(candidates)
                self.former = [f for f in self.former if f[0] != pernr]
                emp = self.employees[pernr]
                persg = self._draw_contract(dept)
                self._start(emp, hire, persg, "rehire", ref.MASSN_REHIRE, "01", dept,
                            self._draw_level(dept, emp.gender, persg), self._draw_empct(dept, emp.gender, persg))
                return
        persg = self._draw_contract(dept)
        gender = self._draw_gender(dept)
        age = self._draw_age_at_hire(persg)
        emp = self._new_employee(dept, hire - timedelta(days=int(age * 365.25)), gender)
        self._start(emp, hire, persg, "hire", ref.MASSN_HIRE, massg, dept,
                    self._draw_level(dept, gender, persg), self._draw_empct(dept, gender, persg))

    def _seasonal_hires(self, year: int) -> None:
        for dept in ref.DEPARTMENTS:
            if not dept.seasonal:
                continue
            for _ in range(round(dept.size * SEASONAL_HIRE_SHARE)):
                hire = self.cal.random_working_day(self.rng, date(year, 6, 1), date(year, 6, 20))
                gender = self._draw_gender(dept)
                age = self.rng.triangular(18.0, 30.0, 21.0)
                emp = self._new_employee(dept, hire - timedelta(days=int(age * 365.25)), gender)
                self._start(emp, hire, ref.PERSG_CDD, "hire", ref.MASSN_HIRE, "03", dept, ref.PERSK_STAFF, 100,
                            seasonal=True, contract_end=hire + timedelta(days=self.rng.randint(60, 92)))

    def _lifecycle(self, emp: Employee, first: date, last: date) -> None:
        dept = ref.DEPT_BY_CODE[emp.state.dept]
        if emp.hired_on is not None and emp.hired_on >= first:
            return  # nothing else happens in the hiring month
        persg = emp.state.persg

        if persg in (ref.PERSG_CDD, ref.PERSG_APPRENTICE) and emp.contract_end is not None and emp.contract_end <= last:
            end = max(emp.contract_end, emp.last_begda)
            kind = "seasonal" if emp.seasonal else "cdd" if persg == ref.PERSG_CDD else "apprentice"
            if self.rng.random() < CONVERSION_PROB[kind]:
                massg = "01" if persg == ref.PERSG_CDD else "02"
                state = replace(emp.state, persg=ref.PERSG_CDI)
                if self._add(emp, Event(end + timedelta(days=1), "contract_change", state,
                                        ref.MASSN_CONTRACT_CHANGE, massg)):
                    emp.contract_end = None
                    emp.seasonal = False
            else:
                self._exit(emp, end, ref.EXIT_CDD_END if persg == ref.PERSG_CDD else ref.EXIT_APPRENTICE_END)
            return

        if persg == ref.PERSG_CDI:
            age = emp.age_on(last)
            if age >= RETIREMENT_MAX_AGE or (age >= RETIREMENT_MIN_AGE and self.rng.random() < _monthly(RETIREMENT_ANNUAL_PROB)):
                self._exit(emp, last, ref.EXIT_RETIREMENT)
                return
            if self.rng.random() < _monthly(dept.cdi_exit_rate):
                day = self.cal.random_working_day(self.rng, max(first, emp.last_begda), last)
                if day is not None:
                    self._exit(emp, day, _weighted(self.rng, CDI_EXIT_REASONS))
                    return
            tenure_ok = emp.hired_on is not None and (first - emp.hired_on).days > 365
            if tenure_ok and self.rng.random() < TRANSFER_MONTHLY_PROB:
                target = _weighted(self.rng, [(d, d.size) for d in ref.DEPARTMENTS if d.code != dept.code])
                state = replace(emp.state, dept=target.code, position=self._new_position())
                self._add(emp, Event(first, "org_change", state, ref.MASSN_ORG_CHANGE, "01"))
            elif emp.state.persk in PROMOTION_MONTHLY_PROB and self.rng.random() < PROMOTION_MONTHLY_PROB[emp.state.persk]:
                new_level = ref.PERSK_SUPERVISOR if emp.state.persk == ref.PERSK_STAFF else ref.PERSK_MANAGER
                state = replace(emp.state, persk=new_level, position=self._new_position())
                self._add(emp, Event(first, "org_change", state, ref.MASSN_ORG_CHANGE, "02"))

        if persg != ref.PERSG_APPRENTICE and self.rng.random() < WORKTIME_CHANGE_MONTHLY_PROB:
            options = [v for v in (100, 90, 80, 50) if v != emp.state.empct]
            self._add(emp, Event(first, "worktime", replace(emp.state, empct=self.rng.choice(options))))

    def _schedule_replacements(self, month_index: int, current: date) -> None:
        years_elapsed = (current - self.config.history_start).days / 365.25
        pending_by_dept: dict[str, int] = {}
        for items in self.pending.values():
            for dept_code, _ in items:
                pending_by_dept[dept_code] = pending_by_dept.get(dept_code, 0) + 1
        active_by_dept: dict[str, int] = {}
        for emp in self.active.values():
            if not emp.seasonal:
                active_by_dept[emp.state.dept] = active_by_dept.get(emp.state.dept, 0) + 1
        for dept in ref.DEPARTMENTS:
            target = round(dept.size * (1 + dept.growth_per_year * years_elapsed))
            staffing = round(target * STAFFING_BUFFER)
            deficit = staffing - active_by_dept.get(dept.code, 0) - pending_by_dept.get(dept.code, 0)
            for _ in range(max(0, deficit)):
                massg = "01"
                if self.created_positions[dept.code] < target - dept.size:
                    massg = "02"
                    self.created_positions[dept.code] += 1
                delay = self.rng.choice([1, 1, 2, 2, 3])
                when = add_months(current, delay)
                if when.month in (7, 8) and self.rng.random() < 0.5:
                    when = date(when.year, 9, 1)
                elif when.month == 12 and self.rng.random() < 0.5:
                    when = date(when.year + 1, 1, 1)
                idx = when.year * 12 + when.month - 1
                self.pending.setdefault(idx, []).append((dept.code, massg))

    def run(self) -> dict[str, Employee]:
        self._create_stock()
        current = self.config.history_start
        last_month = date(self.config.as_of_date.year, self.config.as_of_date.month, 1)
        while current <= last_month:
            first, last = current, month_end(current)
            idx = current.year * 12 + current.month - 1
            for dept_code, massg in self.pending.pop(idx, []):
                self._hire(ref.DEPT_BY_CODE[dept_code], massg, current.year, current.month)
            for pernr in sorted(self.active):
                emp = self.active.get(pernr)
                if emp is not None:
                    self._lifecycle(emp, first, last)
            if current.month == 6:
                self._seasonal_hires(current.year)
            self._schedule_replacements(idx, current)
            current = add_months(current, 1)
        return self.employees


def truncate_history(employees: dict[str, Employee], as_of: date) -> dict[str, Employee]:
    """Keep only events known at the as-of date; drop employees with no remaining event."""
    result = {}
    for pernr, emp in employees.items():
        events = [e for e in emp.events if e.effective_date <= as_of]
        if events:
            result[pernr] = replace(emp, events=events, state=events[-1].state, active=events[-1].kind != "exit")
    return result


def simulate(config: GeneratorConfig, calendar: WorkCalendar) -> dict[str, Employee]:
    employees = PopulationSimulator(config, calendar).run()
    return truncate_history(employees, config.as_of_date)


def poisson(rng: random.Random, lam: float) -> int:
    threshold, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= threshold:
            return k
        k += 1
