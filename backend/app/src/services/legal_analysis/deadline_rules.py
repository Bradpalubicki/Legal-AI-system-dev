"""
Legal Filing Deadline Calculation Engine
Implements FRCP 6(a) day calculation rules and federal/state court deadline rules

This module handles:
- Federal court deadline calculations (FRCP)
- State court deadline calculations (CA, NY, TX, FL, IL)
- Holiday calendar integration
- CM/ECF electronic filing service rules
- Weekend and holiday adjustments
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, Dict, List, Set, Tuple, Callable
import calendar


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class JurisdictionType(Enum):
    """Court jurisdiction types"""
    FEDERAL = "federal"
    STATE_CA = "state_ca"
    STATE_NY = "state_ny"
    STATE_TX = "state_tx"
    STATE_FL = "state_fl"
    STATE_IL = "state_il"
    BANKRUPTCY = "bankruptcy"


class DeadlineType(Enum):
    """Types of legal deadlines"""
    RESPONSE = "response"           # Response to complaint/motion
    ANSWER = "answer"               # Answer to complaint
    DISCOVERY = "discovery"         # Discovery deadlines
    MOTION = "motion"               # Motion filing deadlines
    APPEAL = "appeal"               # Appeal filing deadlines
    SERVICE = "service"             # Service of process deadlines
    DISPOSITIVE = "dispositive"     # Dispositive motion deadlines
    SCHEDULING = "scheduling"       # Scheduling conference deadlines
    EXPERT = "expert"               # Expert disclosure deadlines
    TRIAL = "trial"                 # Trial-related deadlines
    ADMINISTRATIVE = "administrative"  # Administrative deadlines


class ServiceMethod(Enum):
    """Methods of service affecting deadline calculation"""
    ELECTRONIC = "electronic"       # CM/ECF electronic service
    PERSONAL = "personal"           # Personal service
    MAIL = "mail"                   # US Mail service
    OVERNIGHT = "overnight"         # Overnight courier
    FAX = "fax"                     # Fax service
    EMAIL = "email"                 # Email (where permitted)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Holiday:
    """Represents a legal holiday"""
    name: str
    date: date
    federal: bool = True
    states: List[str] = field(default_factory=list)


@dataclass
class DeadlineRule:
    """Represents a deadline calculation rule"""
    name: str
    description: str
    base_days: int
    deadline_type: DeadlineType
    jurisdiction: JurisdictionType
    rule_citation: str

    # Calculation modifiers
    include_trigger_day: bool = False
    exclude_weekends: bool = False  # True for periods < 7 days under FRCP
    exclude_holidays: bool = True
    ends_on_last_business_day: bool = True

    # Service additions
    mail_service_days: int = 3
    electronic_service_days: int = 0

    # Special conditions
    minimum_days: Optional[int] = None
    maximum_days: Optional[int] = None
    notes: str = ""


@dataclass
class CalculatedDeadline:
    """Result of deadline calculation"""
    original_deadline: date
    adjusted_deadline: date
    rule_applied: str
    jurisdiction: JurisdictionType
    calculation_notes: List[str]
    holidays_skipped: List[Holiday]
    weekends_skipped: int
    service_days_added: int
    is_extended: bool
    extension_reason: Optional[str]


# =============================================================================
# FEDERAL HOLIDAY CALENDAR
# =============================================================================

class FederalHolidayCalendar:
    """
    Federal court holiday calendar
    Based on 5 U.S.C. 6103 and FRCP 6(a)(6)
    """

    # Fixed date holidays (month, day)
    FIXED_HOLIDAYS = {
        "New Year's Day": (1, 1),
        "Independence Day": (7, 4),
        "Veterans Day": (11, 11),
        "Christmas Day": (12, 25),
    }

    # Floating holidays (month, weekday, occurrence)
    # weekday: 0=Monday, 6=Sunday
    # occurrence: 1=first, 2=second, -1=last
    FLOATING_HOLIDAYS = {
        "Martin Luther King Jr. Day": (1, 0, 3),      # 3rd Monday in January
        "Presidents Day": (2, 0, 3),                   # 3rd Monday in February
        "Memorial Day": (5, 0, -1),                    # Last Monday in May
        "Labor Day": (9, 0, 1),                        # 1st Monday in September
        "Columbus Day": (10, 0, 2),                    # 2nd Monday in October
        "Thanksgiving Day": (11, 3, 4),                # 4th Thursday in November
    }

    # Juneteenth (added in 2021)
    JUNETEENTH = (6, 19)

    @classmethod
    def get_federal_holidays(cls, year: int) -> List[Holiday]:
        """Get all federal holidays for a given year"""
        holidays = []

        # Fixed holidays
        for name, (month, day) in cls.FIXED_HOLIDAYS.items():
            holiday_date = date(year, month, day)
            # Adjust for weekend observation
            observed_date = cls._adjust_for_weekend(holiday_date)
            holidays.append(Holiday(name=name, date=observed_date, federal=True))

        # Juneteenth
        juneteenth_date = date(year, cls.JUNETEENTH[0], cls.JUNETEENTH[1])
        observed_juneteenth = cls._adjust_for_weekend(juneteenth_date)
        holidays.append(Holiday(name="Juneteenth", date=observed_juneteenth, federal=True))

        # Floating holidays
        for name, (month, weekday, occurrence) in cls.FLOATING_HOLIDAYS.items():
            holiday_date = cls._get_nth_weekday(year, month, weekday, occurrence)
            holidays.append(Holiday(name=name, date=holiday_date, federal=True))

        return sorted(holidays, key=lambda h: h.date)

    @classmethod
    def _adjust_for_weekend(cls, d: date) -> date:
        """
        Adjust fixed holidays for weekend observation
        If Saturday, observe on Friday; if Sunday, observe on Monday
        """
        if d.weekday() == 5:  # Saturday
            return d - timedelta(days=1)
        elif d.weekday() == 6:  # Sunday
            return d + timedelta(days=1)
        return d

    @classmethod
    def _get_nth_weekday(cls, year: int, month: int, weekday: int, n: int) -> date:
        """Get the nth occurrence of a weekday in a month"""
        if n > 0:
            # Count from beginning
            first_day = date(year, month, 1)
            first_weekday = first_day.weekday()

            # Days until first occurrence of target weekday
            days_until = (weekday - first_weekday) % 7
            first_occurrence = first_day + timedelta(days=days_until)

            # Add weeks for nth occurrence
            return first_occurrence + timedelta(weeks=n-1)
        else:
            # Count from end (n=-1 means last)
            # Get last day of month
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            last_weekday = last_day.weekday()
            days_back = (last_weekday - weekday) % 7
            last_occurrence = last_day - timedelta(days=days_back)

            # Go back additional weeks if needed
            return last_occurrence + timedelta(weeks=n+1)

    @classmethod
    def is_federal_holiday(cls, d: date) -> Tuple[bool, Optional[str]]:
        """Check if a date is a federal holiday"""
        holidays = cls.get_federal_holidays(d.year)
        for holiday in holidays:
            if holiday.date == d:
                return True, holiday.name
        return False, None


# =============================================================================
# STATE HOLIDAY CALENDARS
# =============================================================================

class StateHolidayCalendar:
    """State-specific court holiday calendars"""

    # California additional court holidays
    CA_HOLIDAYS = {
        "Cesar Chavez Day": (3, 31),           # March 31
        "Native American Day": "fourth_friday_sept",  # 4th Friday in September
        "Day After Thanksgiving": "day_after_thanksgiving",
    }

    # New York additional court holidays
    NY_HOLIDAYS = {
        "Lincoln's Birthday": (2, 12),
        "Election Day": "first_tuesday_after_first_monday_nov",
    }

    # Texas additional court holidays
    TX_HOLIDAYS = {
        "Confederate Heroes Day": (1, 19),
        "Texas Independence Day": (3, 2),
        "San Jacinto Day": (4, 21),
        "Emancipation Day in Texas": (6, 19),
        "Lyndon Baines Johnson Day": (8, 27),
        "Day After Thanksgiving": "day_after_thanksgiving",
    }

    # Florida court holidays (follows federal mostly)
    FL_HOLIDAYS = {
        "Day After Thanksgiving": "day_after_thanksgiving",
    }

    # Illinois additional court holidays
    IL_HOLIDAYS = {
        "Lincoln's Birthday": (2, 12),
        "Casimir Pulaski Day": "first_monday_march",
        "Day After Thanksgiving": "day_after_thanksgiving",
    }

    @classmethod
    def get_state_holidays(cls, state: str, year: int) -> List[Holiday]:
        """Get state-specific holidays"""
        holidays = []

        state_calendars = {
            "CA": cls.CA_HOLIDAYS,
            "NY": cls.NY_HOLIDAYS,
            "TX": cls.TX_HOLIDAYS,
            "FL": cls.FL_HOLIDAYS,
            "IL": cls.IL_HOLIDAYS,
        }

        state_holidays = state_calendars.get(state.upper(), {})

        for name, date_spec in state_holidays.items():
            if isinstance(date_spec, tuple):
                # Fixed date
                month, day = date_spec
                holiday_date = date(year, month, day)
                observed_date = cls._adjust_for_weekend(holiday_date)
            elif date_spec == "day_after_thanksgiving":
                # Day after Thanksgiving
                thanksgiving = FederalHolidayCalendar._get_nth_weekday(year, 11, 3, 4)
                observed_date = thanksgiving + timedelta(days=1)
            elif date_spec == "fourth_friday_sept":
                # 4th Friday in September
                observed_date = cls._get_nth_weekday(year, 9, 4, 4)
            elif date_spec == "first_monday_march":
                # 1st Monday in March
                observed_date = cls._get_nth_weekday(year, 3, 0, 1)
            elif date_spec == "first_tuesday_after_first_monday_nov":
                # Election Day calculation
                first_monday = cls._get_nth_weekday(year, 11, 0, 1)
                observed_date = first_monday + timedelta(days=1)
            else:
                continue

            holidays.append(Holiday(name=name, date=observed_date, federal=False, states=[state]))

        return holidays

    @classmethod
    def _adjust_for_weekend(cls, d: date) -> date:
        """Adjust for weekend observation"""
        if d.weekday() == 5:  # Saturday
            return d - timedelta(days=1)
        elif d.weekday() == 6:  # Sunday
            return d + timedelta(days=1)
        return d

    @classmethod
    def _get_nth_weekday(cls, year: int, month: int, weekday: int, n: int) -> date:
        """Get nth weekday of month"""
        return FederalHolidayCalendar._get_nth_weekday(year, month, weekday, n)


# =============================================================================
# FEDERAL DEADLINE RULES (FRCP)
# =============================================================================

FEDERAL_DEADLINE_RULES: Dict[str, DeadlineRule] = {
    # Pleadings and Responses
    "answer_complaint": DeadlineRule(
        name="Answer to Complaint",
        description="Time to answer complaint after service",
        base_days=21,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 12(a)(1)(A)(i)",
        notes="21 days after service; 60 days if waiver of service"
    ),
    "answer_complaint_waiver": DeadlineRule(
        name="Answer to Complaint (Waiver)",
        description="Time to answer after waiver of service",
        base_days=60,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 12(a)(1)(A)(ii)",
        notes="60 days from when waiver request was sent"
    ),
    "answer_counterclaim": DeadlineRule(
        name="Answer to Counterclaim",
        description="Time to answer counterclaim",
        base_days=21,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 12(a)(1)(B)",
    ),
    "answer_crossclaim": DeadlineRule(
        name="Answer to Crossclaim",
        description="Time to answer crossclaim",
        base_days=21,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 12(a)(1)(B)",
    ),
    "answer_third_party": DeadlineRule(
        name="Answer to Third-Party Complaint",
        description="Time for third-party defendant to answer",
        base_days=21,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 14(a)(2)(C)",
    ),

    # Motion Responses
    "opposition_motion": DeadlineRule(
        name="Opposition to Motion",
        description="Time to file opposition to motion",
        base_days=14,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="Local Rule (varies by district)",
        notes="Many districts use 14 days; check local rules"
    ),
    "reply_support_motion": DeadlineRule(
        name="Reply in Support of Motion",
        description="Time to file reply brief",
        base_days=7,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="Local Rule (varies by district)",
        exclude_weekends=True,  # < 7 days
    ),
    "response_12b_motion": DeadlineRule(
        name="Response to Rule 12(b) Motion",
        description="Time to respond to dismissal motion",
        base_days=21,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 12(a)(4)",
        notes="If motion denied, 14 days to respond"
    ),

    # Discovery Deadlines
    "initial_disclosures": DeadlineRule(
        name="Initial Disclosures",
        description="Time to serve initial disclosures",
        base_days=14,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(a)(1)(C)",
        notes="14 days after Rule 26(f) conference"
    ),
    "response_interrogatories": DeadlineRule(
        name="Response to Interrogatories",
        description="Time to respond to interrogatories",
        base_days=30,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 33(b)(2)",
    ),
    "response_document_requests": DeadlineRule(
        name="Response to Document Requests",
        description="Time to respond to requests for production",
        base_days=30,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 34(b)(2)(A)",
    ),
    "response_admissions": DeadlineRule(
        name="Response to Requests for Admission",
        description="Time to respond to requests for admission",
        base_days=30,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 36(a)(3)",
        notes="Deemed admitted if no timely response"
    ),
    "objection_subpoena": DeadlineRule(
        name="Objection to Subpoena",
        description="Time to object to document subpoena",
        base_days=14,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 45(d)(2)(B)",
        notes="Before compliance deadline"
    ),
    "motion_compel_discovery": DeadlineRule(
        name="Motion to Compel",
        description="Time to file motion to compel after discovery dispute",
        base_days=30,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 37(a)",
        notes="Varies by district; good faith meet and confer required"
    ),

    # Expert Discovery
    "expert_disclosure_plaintiff": DeadlineRule(
        name="Plaintiff Expert Disclosure",
        description="Plaintiff's expert disclosure deadline",
        base_days=90,
        deadline_type=DeadlineType.EXPERT,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(a)(2)(D)",
        notes="90 days before trial or as ordered"
    ),
    "expert_disclosure_defendant": DeadlineRule(
        name="Defendant Expert Disclosure",
        description="Defendant's expert disclosure deadline",
        base_days=30,
        deadline_type=DeadlineType.EXPERT,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(a)(2)(D)",
        notes="30 days after plaintiff's disclosure"
    ),
    "expert_rebuttal": DeadlineRule(
        name="Rebuttal Expert Disclosure",
        description="Rebuttal expert disclosure deadline",
        base_days=30,
        deadline_type=DeadlineType.EXPERT,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(a)(2)(D)(ii)",
    ),

    # Summary Judgment
    "summary_judgment_motion": DeadlineRule(
        name="Summary Judgment Motion",
        description="Time to file summary judgment motion",
        base_days=30,
        deadline_type=DeadlineType.DISPOSITIVE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 56(b)",
        notes="30 days after close of discovery unless otherwise ordered"
    ),
    "summary_judgment_opposition": DeadlineRule(
        name="Summary Judgment Opposition",
        description="Time to file opposition to summary judgment",
        base_days=21,
        deadline_type=DeadlineType.DISPOSITIVE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 56(c)(1)",
        notes="Varies by district local rules"
    ),

    # Appeals
    "notice_appeal_civil": DeadlineRule(
        name="Notice of Appeal (Civil)",
        description="Time to file notice of appeal in civil case",
        base_days=30,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 4(a)(1)(A)",
        notes="JURISDICTIONAL - cannot be extended"
    ),
    "notice_appeal_usa": DeadlineRule(
        name="Notice of Appeal (USA Party)",
        description="Time to file notice of appeal when USA is party",
        base_days=60,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 4(a)(1)(B)",
        notes="JURISDICTIONAL - cannot be extended"
    ),
    "notice_appeal_criminal": DeadlineRule(
        name="Notice of Appeal (Criminal)",
        description="Time to file notice of appeal in criminal case",
        base_days=14,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 4(b)(1)(A)",
        notes="JURISDICTIONAL - cannot be extended"
    ),
    "appeal_brief_appellant": DeadlineRule(
        name="Appellant's Brief",
        description="Time to file appellant's opening brief",
        base_days=40,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 31(a)(1)",
        notes="After record filed; can be extended"
    ),
    "appeal_brief_appellee": DeadlineRule(
        name="Appellee's Brief",
        description="Time to file appellee's response brief",
        base_days=30,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 31(a)(1)",
        notes="After appellant's brief served"
    ),
    "appeal_brief_reply": DeadlineRule(
        name="Reply Brief",
        description="Time to file appellant's reply brief",
        base_days=21,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 31(a)(1)",
    ),
    "petition_rehearing": DeadlineRule(
        name="Petition for Rehearing",
        description="Time to file petition for panel rehearing",
        base_days=14,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 40(a)(1)",
    ),
    "petition_rehearing_en_banc": DeadlineRule(
        name="Petition for Rehearing En Banc",
        description="Time to file petition for rehearing en banc",
        base_days=14,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRAP 35(c)",
    ),
    "petition_certiorari": DeadlineRule(
        name="Petition for Certiorari",
        description="Time to file petition for writ of certiorari",
        base_days=90,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="Sup. Ct. R. 13.1",
        notes="From entry of judgment or denial of rehearing"
    ),

    # Post-Judgment Motions
    "motion_new_trial": DeadlineRule(
        name="Motion for New Trial",
        description="Time to file motion for new trial",
        base_days=28,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 59(b)",
        notes="No extensions beyond 28 days"
    ),
    "motion_alter_judgment": DeadlineRule(
        name="Motion to Alter/Amend Judgment",
        description="Time to file motion to alter or amend judgment",
        base_days=28,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 59(e)",
        notes="No extensions beyond 28 days"
    ),
    "motion_relief_judgment": DeadlineRule(
        name="Motion for Relief from Judgment",
        description="Time to file Rule 60(b) motion",
        base_days=365,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 60(c)(1)",
        notes="Within 1 year for 60(b)(1)-(3); reasonable time for others"
    ),

    # Service of Process
    "service_summons": DeadlineRule(
        name="Service of Summons",
        description="Time to serve summons and complaint",
        base_days=90,
        deadline_type=DeadlineType.SERVICE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 4(m)",
        notes="Court may extend for good cause"
    ),
    "waiver_service_return": DeadlineRule(
        name="Return Waiver of Service",
        description="Time for defendant to return waiver of service",
        base_days=30,
        deadline_type=DeadlineType.SERVICE,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 4(d)(1)(F)",
        notes="60 days if outside US"
    ),

    # Scheduling
    "rule_26f_conference": DeadlineRule(
        name="Rule 26(f) Conference",
        description="Parties' planning conference deadline",
        base_days=21,
        deadline_type=DeadlineType.SCHEDULING,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(f)(1)",
        notes="At least 21 days before scheduling conference"
    ),
    "scheduling_report": DeadlineRule(
        name="Scheduling Report",
        description="Time to submit discovery plan/scheduling report",
        base_days=14,
        deadline_type=DeadlineType.SCHEDULING,
        jurisdiction=JurisdictionType.FEDERAL,
        rule_citation="FRCP 26(f)(2)",
        notes="14 days after Rule 26(f) conference"
    ),
}


# =============================================================================
# STATE DEADLINE RULES
# =============================================================================

CALIFORNIA_DEADLINE_RULES: Dict[str, DeadlineRule] = {
    "answer_complaint_ca": DeadlineRule(
        name="Answer to Complaint (CA)",
        description="Time to answer complaint in California",
        base_days=30,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 412.20(a)(3)",
        mail_service_days=5,
    ),
    "demurrer_ca": DeadlineRule(
        name="Demurrer (CA)",
        description="Time to file demurrer in California",
        base_days=30,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 430.40(a)",
    ),
    "opposition_motion_ca": DeadlineRule(
        name="Opposition to Motion (CA)",
        description="Time to file opposition in California",
        base_days=9,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 1005(b)",
        exclude_weekends=True,  # Court days
        notes="9 court days before hearing"
    ),
    "reply_motion_ca": DeadlineRule(
        name="Reply to Opposition (CA)",
        description="Time to file reply in California",
        base_days=5,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 1005(b)",
        exclude_weekends=True,  # Court days
        notes="5 court days before hearing"
    ),
    "discovery_response_ca": DeadlineRule(
        name="Discovery Response (CA)",
        description="Time to respond to discovery in California",
        base_days=30,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 2030.260(a)",
        mail_service_days=5,
    ),
    "notice_appeal_ca": DeadlineRule(
        name="Notice of Appeal (CA)",
        description="Time to file notice of appeal in California",
        base_days=60,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CRC 8.104(a)(1)",
        notes="JURISDICTIONAL"
    ),
    "motion_new_trial_ca": DeadlineRule(
        name="Motion for New Trial (CA)",
        description="Time to file motion for new trial in California",
        base_days=15,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.STATE_CA,
        rule_citation="CCP 659(a)",
        notes="15 days after mailing of notice of entry"
    ),
}

NEW_YORK_DEADLINE_RULES: Dict[str, DeadlineRule] = {
    "answer_complaint_ny": DeadlineRule(
        name="Answer to Complaint (NY)",
        description="Time to answer complaint in New York",
        base_days=20,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 3012(a)",
        notes="30 days if service by mail"
    ),
    "answer_complaint_ny_mail": DeadlineRule(
        name="Answer to Complaint (NY-Mail)",
        description="Time to answer complaint served by mail in NY",
        base_days=30,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 3012(a)",
    ),
    "motion_dismiss_ny": DeadlineRule(
        name="Motion to Dismiss (NY)",
        description="Time to file motion to dismiss in New York",
        base_days=20,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 3211(e)",
        notes="Before or with answer"
    ),
    "discovery_response_ny": DeadlineRule(
        name="Discovery Response (NY)",
        description="Time to respond to discovery in New York",
        base_days=20,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 3122(a)(1)",
    ),
    "notice_appeal_ny": DeadlineRule(
        name="Notice of Appeal (NY)",
        description="Time to file notice of appeal in New York",
        base_days=30,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 5513(a)",
        notes="JURISDICTIONAL"
    ),
    "motion_reargument_ny": DeadlineRule(
        name="Motion for Reargument (NY)",
        description="Time to file motion for reargument in New York",
        base_days=30,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.STATE_NY,
        rule_citation="CPLR 2221(d)(3)",
    ),
}

TEXAS_DEADLINE_RULES: Dict[str, DeadlineRule] = {
    "answer_complaint_tx": DeadlineRule(
        name="Answer to Petition (TX)",
        description="Time to answer original petition in Texas",
        base_days=20,
        deadline_type=DeadlineType.ANSWER,
        jurisdiction=JurisdictionType.STATE_TX,
        rule_citation="TRCP 99(b)",
        notes="Monday following 20 days after service"
    ),
    "response_motion_tx": DeadlineRule(
        name="Response to Motion (TX)",
        description="Time to respond to motion in Texas",
        base_days=21,
        deadline_type=DeadlineType.RESPONSE,
        jurisdiction=JurisdictionType.STATE_TX,
        rule_citation="TRCP 21(a)",
        notes="7 days before hearing if no response time set"
    ),
    "discovery_response_tx": DeadlineRule(
        name="Discovery Response (TX)",
        description="Time to respond to discovery in Texas",
        base_days=30,
        deadline_type=DeadlineType.DISCOVERY,
        jurisdiction=JurisdictionType.STATE_TX,
        rule_citation="TRCP 196.2(a)",
    ),
    "notice_appeal_tx": DeadlineRule(
        name="Notice of Appeal (TX)",
        description="Time to file notice of appeal in Texas",
        base_days=30,
        deadline_type=DeadlineType.APPEAL,
        jurisdiction=JurisdictionType.STATE_TX,
        rule_citation="TRAP 26.1(a)",
        notes="90 days if motion for new trial timely filed"
    ),
    "motion_new_trial_tx": DeadlineRule(
        name="Motion for New Trial (TX)",
        description="Time to file motion for new trial in Texas",
        base_days=30,
        deadline_type=DeadlineType.MOTION,
        jurisdiction=JurisdictionType.STATE_TX,
        rule_citation="TRCP 329b(a)",
    ),
}


# =============================================================================
# DEADLINE CALCULATOR
# =============================================================================

class DeadlineCalculator:
    """
    Calculate legal deadlines following FRCP 6(a) and state-specific rules

    FRCP 6(a) Day Calculation Rules:
    1. Exclude the trigger day (day event occurs)
    2. Count every day including weekends/holidays
    3. If period < 7 days, exclude weekends and holidays from count
    4. If last day is weekend/holiday, deadline extends to next business day
    5. Electronic filing: if filed before midnight court time, counts as that day
    """

    def __init__(self, jurisdiction: JurisdictionType = JurisdictionType.FEDERAL):
        self.jurisdiction = jurisdiction
        self._holiday_cache: Dict[int, List[Holiday]] = {}

    def get_holidays_for_year(self, year: int) -> List[Holiday]:
        """Get all applicable holidays for a year"""
        if year in self._holiday_cache:
            return self._holiday_cache[year]

        holidays = FederalHolidayCalendar.get_federal_holidays(year)

        # Add state holidays if applicable
        state_mapping = {
            JurisdictionType.STATE_CA: "CA",
            JurisdictionType.STATE_NY: "NY",
            JurisdictionType.STATE_TX: "TX",
            JurisdictionType.STATE_FL: "FL",
            JurisdictionType.STATE_IL: "IL",
        }

        if self.jurisdiction in state_mapping:
            state = state_mapping[self.jurisdiction]
            state_holidays = StateHolidayCalendar.get_state_holidays(state, year)
            holidays.extend(state_holidays)

        self._holiday_cache[year] = holidays
        return holidays

    def is_business_day(self, d: date) -> bool:
        """Check if a date is a business day (not weekend or holiday)"""
        # Check weekend
        if d.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Check holidays
        holidays = self.get_holidays_for_year(d.year)
        for holiday in holidays:
            if holiday.date == d:
                return False

        return True

    def next_business_day(self, d: date) -> date:
        """Get the next business day after a date"""
        next_day = d + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def previous_business_day(self, d: date) -> date:
        """Get the previous business day before a date"""
        prev_day = d - timedelta(days=1)
        while not self.is_business_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day

    def calculate_deadline(
        self,
        trigger_date: date,
        rule: DeadlineRule,
        service_method: ServiceMethod = ServiceMethod.ELECTRONIC
    ) -> CalculatedDeadline:
        """
        Calculate a deadline based on trigger date and rule

        Args:
            trigger_date: The date the triggering event occurred
            rule: The deadline rule to apply
            service_method: Method of service (affects additional days)

        Returns:
            CalculatedDeadline with all calculation details
        """
        notes = []
        holidays_skipped = []
        weekends_skipped = 0

        # Start counting from day after trigger (FRCP 6(a)(1)(A))
        if not rule.include_trigger_day:
            current_date = trigger_date + timedelta(days=1)
            notes.append(f"Started counting from {current_date} (day after trigger)")
        else:
            current_date = trigger_date
            notes.append(f"Started counting from trigger date {current_date}")

        days_counted = 0
        base_days = rule.base_days

        # Add service days
        service_days = 0
        if service_method == ServiceMethod.MAIL:
            service_days = rule.mail_service_days
        elif service_method == ServiceMethod.ELECTRONIC:
            service_days = rule.electronic_service_days

        total_days_needed = base_days

        # Count days
        if rule.exclude_weekends and base_days < 7:
            # For periods < 7 days, exclude weekends and holidays (FRCP 6(a)(1)(C))
            notes.append(f"Period < 7 days: excluding weekends and holidays")
            while days_counted < total_days_needed:
                if self.is_business_day(current_date):
                    days_counted += 1
                else:
                    if current_date.weekday() >= 5:
                        weekends_skipped += 1
                    else:
                        # Check which holiday
                        holidays = self.get_holidays_for_year(current_date.year)
                        for h in holidays:
                            if h.date == current_date:
                                holidays_skipped.append(h)
                                break

                if days_counted < total_days_needed:
                    current_date += timedelta(days=1)
        else:
            # For periods >= 7 days, count all days (FRCP 6(a)(1)(B))
            current_date += timedelta(days=total_days_needed - 1)
            notes.append(f"Period >= 7 days: counted {total_days_needed} calendar days")

        original_deadline = current_date

        # If deadline falls on weekend/holiday, extend to next business day (FRCP 6(a)(1)(C))
        adjusted_deadline = current_date
        is_extended = False
        extension_reason = None

        if rule.ends_on_last_business_day and not self.is_business_day(adjusted_deadline):
            original_for_note = adjusted_deadline

            # Track what we're skipping
            while not self.is_business_day(adjusted_deadline):
                if adjusted_deadline.weekday() >= 5:
                    weekends_skipped += 1
                else:
                    holidays = self.get_holidays_for_year(adjusted_deadline.year)
                    for h in holidays:
                        if h.date == adjusted_deadline:
                            holidays_skipped.append(h)
                            break
                adjusted_deadline += timedelta(days=1)

            is_extended = True
            extension_reason = f"Extended from {original_for_note} (weekend/holiday) to next business day"
            notes.append(extension_reason)

        # Add service days if applicable
        if service_days > 0:
            adjusted_deadline += timedelta(days=service_days)
            notes.append(f"Added {service_days} days for {service_method.value} service")

            # Re-check if extended deadline falls on weekend/holiday
            if rule.ends_on_last_business_day and not self.is_business_day(adjusted_deadline):
                while not self.is_business_day(adjusted_deadline):
                    adjusted_deadline += timedelta(days=1)
                notes.append("Extended service deadline to next business day")

        return CalculatedDeadline(
            original_deadline=original_deadline,
            adjusted_deadline=adjusted_deadline,
            rule_applied=rule.name,
            jurisdiction=rule.jurisdiction,
            calculation_notes=notes,
            holidays_skipped=holidays_skipped,
            weekends_skipped=weekends_skipped,
            service_days_added=service_days,
            is_extended=is_extended,
            extension_reason=extension_reason
        )

    def calculate_deadline_from_rule_name(
        self,
        trigger_date: date,
        rule_name: str,
        service_method: ServiceMethod = ServiceMethod.ELECTRONIC
    ) -> Optional[CalculatedDeadline]:
        """Calculate deadline using a rule name lookup"""
        rule = get_deadline_rule(rule_name, self.jurisdiction)
        if rule:
            return self.calculate_deadline(trigger_date, rule, service_method)
        return None

    def get_all_related_deadlines(
        self,
        trigger_date: date,
        deadline_type: DeadlineType,
        service_method: ServiceMethod = ServiceMethod.ELECTRONIC
    ) -> List[CalculatedDeadline]:
        """Get all deadlines of a certain type from a trigger date"""
        rules = get_deadline_rules_by_type(deadline_type, self.jurisdiction)
        deadlines = []

        for rule in rules:
            deadline = self.calculate_deadline(trigger_date, rule, service_method)
            deadlines.append(deadline)

        return sorted(deadlines, key=lambda d: d.adjusted_deadline)

    def count_business_days_between(self, start: date, end: date) -> int:
        """Count business days between two dates"""
        if start > end:
            start, end = end, start

        count = 0
        current = start
        while current <= end:
            if self.is_business_day(current):
                count += 1
            current += timedelta(days=1)

        return count

    def add_business_days(self, start: date, days: int) -> date:
        """Add a number of business days to a date"""
        current = start
        days_added = 0

        while days_added < days:
            current += timedelta(days=1)
            if self.is_business_day(current):
                days_added += 1

        return current

    def subtract_business_days(self, start: date, days: int) -> date:
        """Subtract a number of business days from a date"""
        current = start
        days_subtracted = 0

        while days_subtracted < days:
            current -= timedelta(days=1)
            if self.is_business_day(current):
                days_subtracted += 1

        return current


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_all_deadline_rules() -> Dict[str, DeadlineRule]:
    """Get all deadline rules across all jurisdictions"""
    all_rules = {}
    all_rules.update(FEDERAL_DEADLINE_RULES)
    all_rules.update(CALIFORNIA_DEADLINE_RULES)
    all_rules.update(NEW_YORK_DEADLINE_RULES)
    all_rules.update(TEXAS_DEADLINE_RULES)
    return all_rules


def get_deadline_rule(rule_name: str, jurisdiction: JurisdictionType = None) -> Optional[DeadlineRule]:
    """Get a deadline rule by name, optionally filtered by jurisdiction"""
    all_rules = get_all_deadline_rules()

    if rule_name in all_rules:
        rule = all_rules[rule_name]
        if jurisdiction is None or rule.jurisdiction == jurisdiction:
            return rule

    return None


def get_deadline_rules_by_type(
    deadline_type: DeadlineType,
    jurisdiction: JurisdictionType = None
) -> List[DeadlineRule]:
    """Get all deadline rules of a specific type"""
    all_rules = get_all_deadline_rules()

    filtered = []
    for rule in all_rules.values():
        if rule.deadline_type == deadline_type:
            if jurisdiction is None or rule.jurisdiction == jurisdiction:
                filtered.append(rule)

    return filtered


def get_federal_deadline_rules() -> Dict[str, DeadlineRule]:
    """Get all federal deadline rules"""
    return FEDERAL_DEADLINE_RULES


def get_state_deadline_rules(state: str) -> Dict[str, DeadlineRule]:
    """Get deadline rules for a specific state"""
    state_rules = {
        "CA": CALIFORNIA_DEADLINE_RULES,
        "NY": NEW_YORK_DEADLINE_RULES,
        "TX": TEXAS_DEADLINE_RULES,
    }
    return state_rules.get(state.upper(), {})


def parse_deadline_from_text(text: str) -> Optional[Tuple[int, str]]:
    """
    Parse deadline information from text
    Returns tuple of (days, unit) or None
    """
    import re

    patterns = [
        r"(\d+)\s*(?:calendar\s+)?days?",
        r"(\d+)\s*(?:business|court|working)\s+days?",
        r"(\d+)\s*weeks?",
        r"(\d+)\s*months?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            num = int(match.group(1))
            if "week" in pattern:
                return (num * 7, "days")
            elif "month" in pattern:
                return (num * 30, "days")  # Approximate
            elif "business" in match.group(0) or "court" in match.group(0) or "working" in match.group(0):
                return (num, "business_days")
            else:
                return (num, "days")

    return None


def format_deadline_info(deadline: CalculatedDeadline) -> Dict:
    """Format deadline calculation for display or API response"""
    return {
        "original_deadline": deadline.original_deadline.isoformat(),
        "adjusted_deadline": deadline.adjusted_deadline.isoformat(),
        "rule_applied": deadline.rule_applied,
        "jurisdiction": deadline.jurisdiction.value,
        "is_extended": deadline.is_extended,
        "extension_reason": deadline.extension_reason,
        "holidays_skipped": [
            {"name": h.name, "date": h.date.isoformat()}
            for h in deadline.holidays_skipped
        ],
        "weekends_skipped": deadline.weekends_skipped,
        "service_days_added": deadline.service_days_added,
        "calculation_notes": deadline.calculation_notes,
        "days_until_deadline": (deadline.adjusted_deadline - date.today()).days,
    }


# =============================================================================
# SPECIALIZED DEADLINE CALCULATORS
# =============================================================================

class ResponseDeadlineCalculator:
    """Calculate response deadlines for specific filing types"""

    @staticmethod
    def calculate_answer_deadline(
        service_date: date,
        jurisdiction: JurisdictionType,
        waiver: bool = False,
        service_method: ServiceMethod = ServiceMethod.PERSONAL
    ) -> CalculatedDeadline:
        """Calculate deadline to answer a complaint"""
        calculator = DeadlineCalculator(jurisdiction)

        if jurisdiction == JurisdictionType.FEDERAL:
            rule_name = "answer_complaint_waiver" if waiver else "answer_complaint"
        elif jurisdiction == JurisdictionType.STATE_CA:
            rule_name = "answer_complaint_ca"
        elif jurisdiction == JurisdictionType.STATE_NY:
            if service_method == ServiceMethod.MAIL:
                rule_name = "answer_complaint_ny_mail"
            else:
                rule_name = "answer_complaint_ny"
        elif jurisdiction == JurisdictionType.STATE_TX:
            rule_name = "answer_complaint_tx"
        else:
            rule_name = "answer_complaint"

        rule = get_deadline_rule(rule_name, jurisdiction)
        if rule:
            return calculator.calculate_deadline(service_date, rule, service_method)

        return None

    @staticmethod
    def calculate_discovery_response_deadline(
        service_date: date,
        jurisdiction: JurisdictionType,
        service_method: ServiceMethod = ServiceMethod.ELECTRONIC
    ) -> CalculatedDeadline:
        """Calculate deadline to respond to discovery"""
        calculator = DeadlineCalculator(jurisdiction)

        rule_mapping = {
            JurisdictionType.FEDERAL: "response_interrogatories",
            JurisdictionType.STATE_CA: "discovery_response_ca",
            JurisdictionType.STATE_NY: "discovery_response_ny",
            JurisdictionType.STATE_TX: "discovery_response_tx",
        }

        rule_name = rule_mapping.get(jurisdiction, "response_interrogatories")
        rule = get_deadline_rule(rule_name, jurisdiction)

        if rule:
            return calculator.calculate_deadline(service_date, rule, service_method)

        return None

    @staticmethod
    def calculate_appeal_deadline(
        judgment_date: date,
        jurisdiction: JurisdictionType,
        usa_party: bool = False,
        criminal: bool = False
    ) -> CalculatedDeadline:
        """Calculate deadline to file notice of appeal"""
        calculator = DeadlineCalculator(jurisdiction)

        if jurisdiction == JurisdictionType.FEDERAL:
            if criminal:
                rule_name = "notice_appeal_criminal"
            elif usa_party:
                rule_name = "notice_appeal_usa"
            else:
                rule_name = "notice_appeal_civil"
        elif jurisdiction == JurisdictionType.STATE_CA:
            rule_name = "notice_appeal_ca"
        elif jurisdiction == JurisdictionType.STATE_NY:
            rule_name = "notice_appeal_ny"
        elif jurisdiction == JurisdictionType.STATE_TX:
            rule_name = "notice_appeal_tx"
        else:
            rule_name = "notice_appeal_civil"

        rule = get_deadline_rule(rule_name, jurisdiction)
        if rule:
            return calculator.calculate_deadline(judgment_date, rule)

        return None


class AppealBriefCalculator:
    """Calculate appeal brief deadlines"""

    @staticmethod
    def calculate_appellant_brief_deadline(
        record_filed_date: date,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL
    ) -> CalculatedDeadline:
        """Calculate deadline for appellant's opening brief"""
        calculator = DeadlineCalculator(jurisdiction)
        rule = get_deadline_rule("appeal_brief_appellant", jurisdiction)

        if rule:
            return calculator.calculate_deadline(record_filed_date, rule)
        return None

    @staticmethod
    def calculate_appellee_brief_deadline(
        appellant_brief_served_date: date,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL
    ) -> CalculatedDeadline:
        """Calculate deadline for appellee's response brief"""
        calculator = DeadlineCalculator(jurisdiction)
        rule = get_deadline_rule("appeal_brief_appellee", jurisdiction)

        if rule:
            return calculator.calculate_deadline(appellant_brief_served_date, rule)
        return None

    @staticmethod
    def calculate_reply_brief_deadline(
        appellee_brief_served_date: date,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL
    ) -> CalculatedDeadline:
        """Calculate deadline for appellant's reply brief"""
        calculator = DeadlineCalculator(jurisdiction)
        rule = get_deadline_rule("appeal_brief_reply", jurisdiction)

        if rule:
            return calculator.calculate_deadline(appellee_brief_served_date, rule)
        return None

    @staticmethod
    def get_full_briefing_schedule(
        record_filed_date: date,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL
    ) -> Dict[str, CalculatedDeadline]:
        """Get complete briefing schedule from record filing"""
        schedule = {}

        # Appellant's brief
        appellant = AppealBriefCalculator.calculate_appellant_brief_deadline(
            record_filed_date, jurisdiction
        )
        if appellant:
            schedule["appellant_brief"] = appellant

            # Appellee's brief (30 days after appellant's brief)
            appellee = AppealBriefCalculator.calculate_appellee_brief_deadline(
                appellant.adjusted_deadline, jurisdiction
            )
            if appellee:
                schedule["appellee_brief"] = appellee

                # Reply brief
                reply = AppealBriefCalculator.calculate_reply_brief_deadline(
                    appellee.adjusted_deadline, jurisdiction
                )
                if reply:
                    schedule["reply_brief"] = reply

        return schedule


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "JurisdictionType",
    "DeadlineType",
    "ServiceMethod",

    # Data classes
    "Holiday",
    "DeadlineRule",
    "CalculatedDeadline",

    # Holiday calendars
    "FederalHolidayCalendar",
    "StateHolidayCalendar",

    # Rule collections
    "FEDERAL_DEADLINE_RULES",
    "CALIFORNIA_DEADLINE_RULES",
    "NEW_YORK_DEADLINE_RULES",
    "TEXAS_DEADLINE_RULES",

    # Main calculator
    "DeadlineCalculator",

    # Specialized calculators
    "ResponseDeadlineCalculator",
    "AppealBriefCalculator",

    # Utility functions
    "get_all_deadline_rules",
    "get_deadline_rule",
    "get_deadline_rules_by_type",
    "get_federal_deadline_rules",
    "get_state_deadline_rules",
    "parse_deadline_from_text",
    "format_deadline_info",
]
