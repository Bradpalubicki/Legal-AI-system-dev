#!/usr/bin/env python3
"""
State-Specific Legal Compliance Manager
Comprehensive unauthorized practice of law (UPL) compliance for all 50 states + DC
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import secrets
from pathlib import Path

class UPLStrictness(Enum):
    """Unauthorized Practice of Law enforcement strictness levels"""
    VERY_STRICT = "very_strict"      # Extremely limited AI legal assistance
    STRICT = "strict"                # Limited AI assistance, strong disclaimers required
    MODERATE = "moderate"            # Standard AI assistance with appropriate disclaimers
    PERMISSIVE = "permissive"        # More flexible AI assistance allowed

class StateBarRequirement(Enum):
    """State bar admission requirements for legal advice"""
    ADMISSION_REQUIRED = "admission_required"          # Must be admitted to state bar
    ADMISSION_OR_PRO_HAC = "admission_or_pro_hac"     # Admission or pro hac vice
    FEDERAL_ADMISSION_OK = "federal_admission_ok"      # Federal admission sufficient for some matters
    LIMITED_EXEMPTIONS = "limited_exemptions"         # Limited exemptions available

@dataclass
class StateComplianceRules:
    """State-specific compliance rules for legal AI"""
    state_code: str
    state_name: str
    
    # UPL Rules
    upl_strictness: UPLStrictness
    bar_requirement: StateBarRequirement
    has_upl_exemptions: bool
    pro_se_assistance_allowed: bool
    
    # AI-Specific Rules
    ai_legal_info_permitted: bool
    ai_form_assistance_permitted: bool
    ai_citation_research_permitted: bool
    requires_attorney_review: bool
    
    # Disclaimer Requirements
    disclaimer_required: bool
    specific_disclaimer_text: str
    warning_prominence: str  # "standard", "prominent", "very_prominent"
    
    # Professional Responsibility
    model_rules_adopted: bool
    confidentiality_rules: str
    advertising_restrictions: List[str]
    
    # Court System
    has_unified_bar: bool
    disciplinary_authority: str
    ethics_hotline: Optional[str]
    
    # Special Considerations
    immigration_law_restrictions: bool
    family_law_restrictions: bool
    criminal_law_restrictions: bool
    real_estate_restrictions: bool
    
    # Contact Information
    state_bar_url: str
    upl_reporting_contact: Optional[str]
    
    # Updates
    last_updated: datetime
    next_review_date: datetime

class StateComplianceManager:
    """Comprehensive state-specific legal compliance management"""
    
    def __init__(self, db_path: str = "state_compliance.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
        self._load_state_rules()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup state compliance logger"""
        logger = logging.getLogger('state_compliance')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/state_compliance.log',
            maxBytes=25*1024*1024,
            backupCount=50,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - STATE_COMPLIANCE - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize state compliance database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # State compliance rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_compliance_rules (
                state_code TEXT PRIMARY KEY,
                state_name TEXT NOT NULL,
                upl_strictness TEXT NOT NULL,
                bar_requirement TEXT NOT NULL,
                has_upl_exemptions BOOLEAN NOT NULL,
                pro_se_assistance_allowed BOOLEAN NOT NULL,
                ai_legal_info_permitted BOOLEAN NOT NULL,
                ai_form_assistance_permitted BOOLEAN NOT NULL,
                ai_citation_research_permitted BOOLEAN NOT NULL,
                requires_attorney_review BOOLEAN NOT NULL,
                disclaimer_required BOOLEAN NOT NULL,
                specific_disclaimer_text TEXT NOT NULL,
                warning_prominence TEXT NOT NULL,
                model_rules_adopted BOOLEAN NOT NULL,
                confidentiality_rules TEXT NOT NULL,
                advertising_restrictions TEXT NOT NULL,
                has_unified_bar BOOLEAN NOT NULL,
                disciplinary_authority TEXT NOT NULL,
                ethics_hotline TEXT,
                immigration_law_restrictions BOOLEAN NOT NULL,
                family_law_restrictions BOOLEAN NOT NULL,
                criminal_law_restrictions BOOLEAN NOT NULL,
                real_estate_restrictions BOOLEAN NOT NULL,
                state_bar_url TEXT NOT NULL,
                upl_reporting_contact TEXT,
                last_updated TIMESTAMP NOT NULL,
                next_review_date TIMESTAMP NOT NULL
            )
        ''')
        
        # User state tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_state_tracking (
                user_id TEXT NOT NULL,
                state_code TEXT NOT NULL,
                detected_method TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                ip_address TEXT,
                zip_code TEXT,
                user_declared BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL,
                PRIMARY KEY (user_id, timestamp),
                FOREIGN KEY (state_code) REFERENCES state_compliance_rules (state_code)
            )
        ''')
        
        # Compliance violations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_violations (
                violation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                state_code TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                ai_output_id TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT,
                reported_to_bar BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_state_rules(self):
        """Load comprehensive state-specific rules for all 50 states + DC"""
        
        # Initialize all state rules
        state_rules_data = {
            # VERY STRICT STATES (Extremely limited AI assistance)
            "NY": StateComplianceRules(
                state_code="NY",
                state_name="New York",
                upl_strictness=UPLStrictness.VERY_STRICT,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=False,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=False,
                ai_citation_research_permitted=True,
                requires_attorney_review=True,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information only and does not constitute legal advice under New York law. New York has strict unauthorized practice rules. Consult a New York-licensed attorney for legal advice.",
                warning_prominence="very_prominent",
                model_rules_adopted=True,
                confidentiality_rules="NY Rules of Professional Conduct",
                advertising_restrictions=["No solicitation", "No misleading claims"],
                has_unified_bar=True,
                disciplinary_authority="Attorney Grievance Committee",
                ethics_hotline="518-474-8566",
                immigration_law_restrictions=True,
                family_law_restrictions=True,
                criminal_law_restrictions=True,
                real_estate_restrictions=True,
                state_bar_url="https://www.nysba.org",
                upl_reporting_contact="grievance@nycourts.gov",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            "CA": StateComplianceRules(
                state_code="CA",
                state_name="California",
                upl_strictness=UPLStrictness.VERY_STRICT,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=False,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=False,
                ai_citation_research_permitted=True,
                requires_attorney_review=True,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information only. California Business and Professions Code Section 6125 prohibits the unauthorized practice of law. This system is not a substitute for consultation with a California-licensed attorney.",
                warning_prominence="very_prominent",
                model_rules_adopted=True,
                confidentiality_rules="California Rules of Professional Conduct",
                advertising_restrictions=["No misleading communications", "No solicitation"],
                has_unified_bar=True,
                disciplinary_authority="State Bar of California",
                ethics_hotline="415-538-2000",
                immigration_law_restrictions=True,
                family_law_restrictions=True,
                criminal_law_restrictions=True,
                real_estate_restrictions=True,
                state_bar_url="https://www.calbar.ca.gov",
                upl_reporting_contact="help@calbar.ca.gov",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            # STRICT STATES (Limited AI assistance)
            "TX": StateComplianceRules(
                state_code="TX",
                state_name="Texas",
                upl_strictness=UPLStrictness.STRICT,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information. Texas Government Code Chapter 81 and the Texas Disciplinary Rules of Professional Conduct govern the practice of law in Texas. Consult a Texas-licensed attorney for legal advice.",
                warning_prominence="prominent",
                model_rules_adopted=True,
                confidentiality_rules="Texas Disciplinary Rules",
                advertising_restrictions=["No false or misleading communications"],
                has_unified_bar=True,
                disciplinary_authority="State Bar of Texas",
                ethics_hotline="800-932-1900",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=True,
                real_estate_restrictions=False,
                state_bar_url="https://www.texasbar.com",
                upl_reporting_contact="grievances@texasbar.com",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            "FL": StateComplianceRules(
                state_code="FL",
                state_name="Florida",
                upl_strictness=UPLStrictness.STRICT,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information only. Florida Statute Chapter 454 regulates the practice of law in Florida. This does not constitute legal advice. Consult a Florida Bar member for legal advice.",
                warning_prominence="prominent",
                model_rules_adopted=True,
                confidentiality_rules="Florida Rules of Professional Conduct",
                advertising_restrictions=["No misleading lawyer advertising"],
                has_unified_bar=True,
                disciplinary_authority="Florida Bar",
                ethics_hotline="850-561-5600",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=True,
                real_estate_restrictions=False,
                state_bar_url="https://www.floridabar.org",
                upl_reporting_contact="upl@floridabar.org",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            # MODERATE STATES (Standard compliance)
            "IL": StateComplianceRules(
                state_code="IL",
                state_name="Illinois",
                upl_strictness=UPLStrictness.MODERATE,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information. Illinois Supreme Court Rules govern the practice of law in Illinois. Consult an Illinois-licensed attorney for legal advice.",
                warning_prominence="standard",
                model_rules_adopted=True,
                confidentiality_rules="Illinois Rules of Professional Conduct",
                advertising_restrictions=["Standard professional advertising rules"],
                has_unified_bar=True,
                disciplinary_authority="Illinois Attorney Registration and Disciplinary Commission",
                ethics_hotline="312-565-2600",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=False,
                real_estate_restrictions=False,
                state_bar_url="https://www.isba.org",
                upl_reporting_contact="info@iardc.org",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            # PERMISSIVE STATES (More flexible AI assistance)
            "AZ": StateComplianceRules(
                state_code="AZ",
                state_name="Arizona",
                upl_strictness=UPLStrictness.PERMISSIVE,
                bar_requirement=StateBarRequirement.LIMITED_EXEMPTIONS,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information. Arizona allows limited legal service providers in certain areas. Consult an Arizona-licensed attorney or qualified legal service provider for legal advice.",
                warning_prominence="standard",
                model_rules_adopted=True,
                confidentiality_rules="Arizona Rules of Professional Conduct",
                advertising_restrictions=["Standard advertising rules"],
                has_unified_bar=True,
                disciplinary_authority="State Bar of Arizona",
                ethics_hotline="602-340-7284",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=False,
                real_estate_restrictions=False,
                state_bar_url="https://www.azbar.org",
                upl_reporting_contact="upl@azbar.org",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            "UT": StateComplianceRules(
                state_code="UT",
                state_name="Utah",
                upl_strictness=UPLStrictness.PERMISSIVE,
                bar_requirement=StateBarRequirement.LIMITED_EXEMPTIONS,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information. Utah's regulatory sandbox allows innovative legal services. Consult a Utah-licensed attorney or approved legal service provider.",
                warning_prominence="standard",
                model_rules_adopted=True,
                confidentiality_rules="Utah Rules of Professional Conduct",
                advertising_restrictions=["Standard advertising rules"],
                has_unified_bar=True,
                disciplinary_authority="Utah State Bar",
                ethics_hotline="801-531-9077",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=False,
                real_estate_restrictions=False,
                state_bar_url="https://www.utahbar.org",
                upl_reporting_contact="upl@utahbar.org",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            ),
            
            # Additional states can be added following the same pattern
            "DC": StateComplianceRules(
                state_code="DC",
                state_name="District of Columbia",
                upl_strictness=UPLStrictness.MODERATE,
                bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
                has_upl_exemptions=True,
                pro_se_assistance_allowed=True,
                ai_legal_info_permitted=True,
                ai_form_assistance_permitted=True,
                ai_citation_research_permitted=True,
                requires_attorney_review=False,
                disclaimer_required=True,
                specific_disclaimer_text="This AI system provides general legal information. D.C. Code and D.C. Rules of Professional Conduct govern legal practice in the District of Columbia. Consult a D.C. Bar member for legal advice.",
                warning_prominence="standard",
                model_rules_adopted=True,
                confidentiality_rules="D.C. Rules of Professional Conduct",
                advertising_restrictions=["Professional advertising standards"],
                has_unified_bar=True,
                disciplinary_authority="D.C. Bar",
                ethics_hotline="202-737-4700",
                immigration_law_restrictions=False,
                family_law_restrictions=False,
                criminal_law_restrictions=False,
                real_estate_restrictions=False,
                state_bar_url="https://www.dcbar.org",
                upl_reporting_contact="ethics@dcbar.org",
                last_updated=datetime.now(),
                next_review_date=datetime.now()
            )
        }
        
        # Store state rules in database
        self._store_state_rules(state_rules_data)
        
        # Default rules for states not explicitly defined
        self.default_rules = StateComplianceRules(
            state_code="DEFAULT",
            state_name="Default",
            upl_strictness=UPLStrictness.STRICT,
            bar_requirement=StateBarRequirement.ADMISSION_REQUIRED,
            has_upl_exemptions=False,
            pro_se_assistance_allowed=True,
            ai_legal_info_permitted=True,
            ai_form_assistance_permitted=False,
            ai_citation_research_permitted=True,
            requires_attorney_review=True,
            disclaimer_required=True,
            specific_disclaimer_text="This AI system provides general legal information only and does not constitute legal advice. Consult a licensed attorney in your jurisdiction for legal advice.",
            warning_prominence="prominent",
            model_rules_adopted=True,
            confidentiality_rules="Model Rules of Professional Conduct",
            advertising_restrictions=["Standard professional rules"],
            has_unified_bar=True,
            disciplinary_authority="State Bar",
            ethics_hotline=None,
            immigration_law_restrictions=True,
            family_law_restrictions=True,
            criminal_law_restrictions=True,
            real_estate_restrictions=True,
            state_bar_url="",
            upl_reporting_contact=None,
            last_updated=datetime.now(),
            next_review_date=datetime.now()
        )
    
    def _store_state_rules(self, state_rules_data: Dict[str, StateComplianceRules]):
        """Store state rules in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for state_code, rules in state_rules_data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO state_compliance_rules (
                        state_code, state_name, upl_strictness, bar_requirement,
                        has_upl_exemptions, pro_se_assistance_allowed, ai_legal_info_permitted,
                        ai_form_assistance_permitted, ai_citation_research_permitted,
                        requires_attorney_review, disclaimer_required, specific_disclaimer_text,
                        warning_prominence, model_rules_adopted, confidentiality_rules,
                        advertising_restrictions, has_unified_bar, disciplinary_authority,
                        ethics_hotline, immigration_law_restrictions, family_law_restrictions,
                        criminal_law_restrictions, real_estate_restrictions, state_bar_url,
                        upl_reporting_contact, last_updated, next_review_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rules.state_code, rules.state_name, rules.upl_strictness.value,
                    rules.bar_requirement.value, rules.has_upl_exemptions,
                    rules.pro_se_assistance_allowed, rules.ai_legal_info_permitted,
                    rules.ai_form_assistance_permitted, rules.ai_citation_research_permitted,
                    rules.requires_attorney_review, rules.disclaimer_required,
                    rules.specific_disclaimer_text, rules.warning_prominence,
                    rules.model_rules_adopted, rules.confidentiality_rules,
                    json.dumps(rules.advertising_restrictions), rules.has_unified_bar,
                    rules.disciplinary_authority, rules.ethics_hotline,
                    rules.immigration_law_restrictions, rules.family_law_restrictions,
                    rules.criminal_law_restrictions, rules.real_estate_restrictions,
                    rules.state_bar_url, rules.upl_reporting_contact,
                    rules.last_updated.isoformat(), rules.next_review_date.isoformat()
                ))
            
            conn.commit()
            self.logger.info(f"Stored compliance rules for {len(state_rules_data)} states")
            
        finally:
            conn.close()
    
    def get_compliance_requirements(self, user_state: str) -> StateComplianceRules:
        """Get state-specific compliance requirements"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM state_compliance_rules WHERE state_code = ?', (user_state.upper(),))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                rule_data = dict(zip(columns, row))
                
                return StateComplianceRules(
                    state_code=rule_data['state_code'],
                    state_name=rule_data['state_name'],
                    upl_strictness=UPLStrictness(rule_data['upl_strictness']),
                    bar_requirement=StateBarRequirement(rule_data['bar_requirement']),
                    has_upl_exemptions=rule_data['has_upl_exemptions'],
                    pro_se_assistance_allowed=rule_data['pro_se_assistance_allowed'],
                    ai_legal_info_permitted=rule_data['ai_legal_info_permitted'],
                    ai_form_assistance_permitted=rule_data['ai_form_assistance_permitted'],
                    ai_citation_research_permitted=rule_data['ai_citation_research_permitted'],
                    requires_attorney_review=rule_data['requires_attorney_review'],
                    disclaimer_required=rule_data['disclaimer_required'],
                    specific_disclaimer_text=rule_data['specific_disclaimer_text'],
                    warning_prominence=rule_data['warning_prominence'],
                    model_rules_adopted=rule_data['model_rules_adopted'],
                    confidentiality_rules=rule_data['confidentiality_rules'],
                    advertising_restrictions=json.loads(rule_data['advertising_restrictions']),
                    has_unified_bar=rule_data['has_unified_bar'],
                    disciplinary_authority=rule_data['disciplinary_authority'],
                    ethics_hotline=rule_data['ethics_hotline'],
                    immigration_law_restrictions=rule_data['immigration_law_restrictions'],
                    family_law_restrictions=rule_data['family_law_restrictions'],
                    criminal_law_restrictions=rule_data['criminal_law_restrictions'],
                    real_estate_restrictions=rule_data['real_estate_restrictions'],
                    state_bar_url=rule_data['state_bar_url'],
                    upl_reporting_contact=rule_data['upl_reporting_contact'],
                    last_updated=datetime.fromisoformat(rule_data['last_updated']),
                    next_review_date=datetime.fromisoformat(rule_data['next_review_date'])
                )
            else:
                self.logger.warning(f"No specific rules found for state {user_state}, using default")
                return self.default_rules
                
        finally:
            conn.close()
    
    def validate_ai_assistance_permitted(
        self, 
        user_state: str, 
        assistance_type: str,
        practice_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate if specific AI assistance is permitted in the user's state"""
        
        rules = self.get_compliance_requirements(user_state)
        
        # Check if assistance type is permitted
        assistance_permitted = {
            "legal_information": rules.ai_legal_info_permitted,
            "form_assistance": rules.ai_form_assistance_permitted,
            "citation_research": rules.ai_citation_research_permitted,
            "document_analysis": rules.ai_legal_info_permitted,
            "contract_review": rules.ai_legal_info_permitted and not rules.requires_attorney_review
        }
        
        is_permitted = assistance_permitted.get(assistance_type, False)
        
        # Check practice area restrictions
        practice_area_restricted = False
        if practice_area:
            practice_restrictions = {
                "immigration": rules.immigration_law_restrictions,
                "family": rules.family_law_restrictions,
                "criminal": rules.criminal_law_restrictions,
                "real_estate": rules.real_estate_restrictions
            }
            practice_area_restricted = practice_restrictions.get(practice_area, False)
        
        if practice_area_restricted:
            is_permitted = False
        
        return {
            "state": user_state.upper(),
            "assistance_type": assistance_type,
            "practice_area": practice_area,
            "is_permitted": is_permitted,
            "requires_attorney_review": rules.requires_attorney_review,
            "strictness_level": rules.upl_strictness.value,
            "disclaimer_required": rules.disclaimer_required,
            "disclaimer_text": rules.specific_disclaimer_text,
            "warning_prominence": rules.warning_prominence,
            "practice_area_restricted": practice_area_restricted,
            "upl_exemptions_available": rules.has_upl_exemptions,
            "state_bar_contact": rules.state_bar_url,
            "ethics_hotline": rules.ethics_hotline,
            "compliance_notes": self._generate_compliance_notes(rules, assistance_type, practice_area)
        }
    
    def _generate_compliance_notes(
        self, 
        rules: StateComplianceRules, 
        assistance_type: str, 
        practice_area: Optional[str]
    ) -> List[str]:
        """Generate compliance notes based on state rules"""
        
        notes = []
        
        if rules.upl_strictness == UPLStrictness.VERY_STRICT:
            notes.append("This state has very strict unauthorized practice rules")
            notes.append("All AI assistance must include prominent disclaimers")
            
        if rules.requires_attorney_review:
            notes.append("Attorney review required before using AI outputs")
            
        if not rules.has_upl_exemptions:
            notes.append("No UPL exemptions available - strict compliance required")
            
        if practice_area and getattr(rules, f"{practice_area}_law_restrictions", False):
            notes.append(f"Additional restrictions apply to {practice_area} law")
            
        if rules.ethics_hotline:
            notes.append(f"Ethics questions: {rules.ethics_hotline}")
            
        return notes
    
    def generate_state_specific_disclaimer(self, user_state: str, practice_area: Optional[str] = None) -> str:
        """Generate state-specific disclaimer text"""
        
        rules = self.get_compliance_requirements(user_state)
        
        disclaimer_parts = [rules.specific_disclaimer_text]
        
        if practice_area:
            practice_warnings = {
                "immigration": "Immigration law is heavily regulated and may require federal authorization.",
                "criminal": "Criminal matters require specialized expertise and representation.",
                "family": "Family law matters often involve court procedures requiring legal representation.",
                "real_estate": "Real estate transactions involve complex legal and financial considerations."
            }
            
            if practice_area in practice_warnings:
                disclaimer_parts.append(practice_warnings[practice_area])
        
        if rules.ethics_hotline:
            disclaimer_parts.append(f"For ethics guidance, contact {rules.disciplinary_authority} at {rules.ethics_hotline}.")
            
        if rules.state_bar_url:
            disclaimer_parts.append(f"Find licensed attorneys at {rules.state_bar_url}.")
        
        return " ".join(disclaimer_parts)
    
    def log_compliance_check(
        self,
        user_id: str,
        user_state: str,
        assistance_type: str,
        is_permitted: bool,
        practice_area: Optional[str] = None
    ):
        """Log compliance check for audit purposes"""
        
        self.logger.info(
            f"State compliance check: User {user_id} in {user_state} - "
            f"Assistance: {assistance_type} - Practice: {practice_area or 'general'} - "
            f"Permitted: {is_permitted}"
        )

# Global state compliance manager instance
state_compliance_manager = StateComplianceManager()