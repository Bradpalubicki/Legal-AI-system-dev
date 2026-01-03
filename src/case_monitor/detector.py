"""
Change Detection Engine

Analyzes PACER docket data to detect meaningful changes including new filings,
status changes, document availability, and other case updates.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import difflib
import re

from .models import (
    ChangeDetection, ChangeType, AlertSeverity, DeltaAnalysis,
    categorize_docket_entry, MonitoredCase
)
from ..pacer_gateway.models import DocketEntry, DocumentInfo


# Configure logging
logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detects and analyzes changes in PACER case data"""
    
    def __init__(self):
        # Keywords for different types of legal documents/actions
        self.motion_keywords = [
            "motion", "application", "petition", "request", "move",
            "seeks", "asks", "applies", "petitions"
        ]
        
        self.order_keywords = [
            "order", "ordered", "orders", "ruling", "rules", "decision",
            "decides", "holds", "finds", "grants", "denies", "dismisses"
        ]
        
        self.judgment_keywords = [
            "judgment", "judgement", "verdict", "award", "damages",
            "final judgment", "summary judgment", "default judgment"
        ]
        
        self.hearing_keywords = [
            "hearing", "conference", "oral argument", "trial", "proceeding",
            "hearing set", "hearing scheduled", "conference set", "trial set"
        ]
        
        self.deadline_keywords = [
            "deadline", "due date", "time limit", "extension", "stay",
            "continued", "postponed", "rescheduled"
        ]
        
        # High-priority keywords that should trigger urgent alerts
        self.urgent_keywords = [
            "emergency", "urgent", "tro", "temporary restraining order",
            "preliminary injunction", "contempt", "sanction", "default"
        ]
        
        logger.info("Change Detector initialized")
    
    def analyze_changes(
        self,
        monitored_case: MonitoredCase,
        current_docket_data: Dict[str, Any],
        current_case_info: Dict[str, Any] = None
    ) -> DeltaAnalysis:
        """Analyze changes between cached and current docket data"""
        
        try:
            logger.debug(f"Analyzing changes for case {monitored_case.case_number}")
            
            # Initialize delta analysis
            analysis = DeltaAnalysis(
                case_number=monitored_case.case_number,
                court_id=monitored_case.court_id,
                analysis_time=datetime.now(timezone.utc),
                old_entry_count=len(monitored_case.cached_docket_entries),
                new_entry_count=len(current_docket_data.get('docket_entries', []))
            )
            
            # Analyze docket entries
            self._analyze_docket_changes(
                monitored_case,
                current_docket_data.get('docket_entries', []),
                analysis
            )
            
            # Analyze case info changes
            if current_case_info:
                self._analyze_case_info_changes(
                    monitored_case,
                    current_case_info,
                    analysis
                )
            
            # Generate change detections
            analysis.detected_changes = self._generate_change_detections(
                monitored_case, analysis
            )
            
            logger.info(
                f"Change analysis completed for {monitored_case.case_number}: "
                f"{analysis.total_changes} changes detected"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Change analysis failed: {str(e)}")
            return DeltaAnalysis(
                case_number=monitored_case.case_number,
                court_id=monitored_case.court_id,
                analysis_time=datetime.now(timezone.utc),
                old_entry_count=0,
                new_entry_count=0
            )
    
    def _analyze_docket_changes(
        self,
        monitored_case: MonitoredCase,
        current_entries: List[Dict[str, Any]],
        analysis: DeltaAnalysis
    ):
        """Analyze changes in docket entries"""
        
        try:
            # Create lookup maps
            old_entries = {entry.get('entry_number', ''): entry 
                          for entry in monitored_case.cached_docket_entries}
            new_entries = {entry.get('entry_number', ''): entry 
                          for entry in current_entries}
            
            # Find added entries
            for entry_number, entry in new_entries.items():
                if entry_number not in old_entries:
                    analysis.added_entries.append(entry)
                    logger.debug(f"New docket entry detected: {entry_number}")
            
            # Find modified entries
            for entry_number, new_entry in new_entries.items():
                if entry_number in old_entries:
                    old_entry = old_entries[entry_number]
                    if self._entries_differ(old_entry, new_entry):
                        analysis.modified_entries.append({
                            'entry_number': entry_number,
                            'old_entry': old_entry,
                            'new_entry': new_entry,
                            'changes': self._get_entry_differences(old_entry, new_entry)
                        })
                        logger.debug(f"Modified docket entry detected: {entry_number}")
            
            # Find removed entries (rare in PACER but possible)
            for entry_number, entry in old_entries.items():
                if entry_number not in new_entries:
                    analysis.removed_entries.append(entry)
                    logger.debug(f"Removed docket entry detected: {entry_number}")
            
            # Analyze document availability changes
            self._analyze_document_changes(old_entries, new_entries, analysis)
            
        except Exception as e:
            logger.error(f"Docket change analysis failed: {str(e)}")
    
    def _analyze_case_info_changes(
        self,
        monitored_case: MonitoredCase,
        current_case_info: Dict[str, Any],
        analysis: DeltaAnalysis
    ):
        """Analyze changes in case information"""
        
        try:
            cached_info = monitored_case.cached_case_info or {}
            
            # Check for significant case info changes
            significant_fields = [
                'case_status', 'judge_name', 'case_title', 'nature_of_suit',
                'cause_of_action', 'parties'
            ]
            
            for field in significant_fields:
                old_value = cached_info.get(field)
                new_value = current_case_info.get(field)
                
                if old_value != new_value:
                    change = {
                        'field': field,
                        'old_value': old_value,
                        'new_value': new_value,
                        'change_type': self._classify_case_info_change(field, old_value, new_value)
                    }
                    analysis.status_changes.append(change)
                    logger.debug(f"Case info change detected: {field}")
            
        except Exception as e:
            logger.error(f"Case info change analysis failed: {str(e)}")
    
    def _analyze_document_changes(
        self,
        old_entries: Dict[str, Dict[str, Any]],
        new_entries: Dict[str, Dict[str, Any]],
        analysis: DeltaAnalysis
    ):
        """Analyze changes in document availability"""
        
        try:
            for entry_number, new_entry in new_entries.items():
                old_entry = old_entries.get(entry_number, {})
                
                # Check for new documents in existing entries
                old_docs = old_entry.get('document_links', [])
                new_docs = new_entry.get('document_links', [])
                
                if len(new_docs) > len(old_docs):
                    new_document_count = len(new_docs) - len(old_docs)
                    
                    for i in range(len(old_docs), len(new_docs)):
                        doc_info = {
                            'entry_number': entry_number,
                            'document_link': new_docs[i],
                            'description': new_entry.get('description', ''),
                            'date_filed': new_entry.get('date_filed', '')
                        }
                        analysis.new_documents.append(doc_info)
                        logger.debug(f"New document detected in entry {entry_number}")
            
        except Exception as e:
            logger.error(f"Document change analysis failed: {str(e)}")
    
    def _entries_differ(self, entry1: Dict[str, Any], entry2: Dict[str, Any]) -> bool:
        """Check if two docket entries are different"""
        
        # Compare key fields
        compare_fields = ['description', 'date_filed', 'document_links']
        
        for field in compare_fields:
            if entry1.get(field) != entry2.get(field):
                return True
        
        return False
    
    def _get_entry_differences(
        self,
        old_entry: Dict[str, Any],
        new_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get specific differences between two entries"""
        
        differences = {}
        
        compare_fields = ['description', 'date_filed', 'document_links']
        
        for field in compare_fields:
            old_val = old_entry.get(field)
            new_val = new_entry.get(field)
            
            if old_val != new_val:
                differences[field] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return differences
    
    def _classify_case_info_change(
        self,
        field: str,
        old_value: Any,
        new_value: Any
    ) -> ChangeType:
        """Classify the type of case info change"""
        
        if field == 'judge_name':
            return ChangeType.JUDGE_CHANGE
        elif field == 'case_status':
            if new_value and 'closed' in str(new_value).lower():
                return ChangeType.CASE_CLOSED
            elif old_value and 'closed' in str(old_value).lower() and new_value:
                return ChangeType.CASE_REOPENED
            else:
                return ChangeType.CASE_STATUS_CHANGE
        elif field == 'parties':
            return ChangeType.PARTY_CHANGE
        else:
            return ChangeType.OTHER
    
    def _generate_change_detections(
        self,
        monitored_case: MonitoredCase,
        analysis: DeltaAnalysis
    ) -> List[ChangeDetection]:
        """Generate change detection objects from analysis"""
        
        detections = []
        
        try:
            # Process added docket entries
            for entry in analysis.added_entries:
                change_types = self._classify_docket_entry(entry)
                
                for change_type in change_types:
                    severity = self._determine_severity(change_type, entry)
                    
                    detection = ChangeDetection(
                        change_id="",  # Will be auto-generated
                        monitor_id=monitored_case.monitor_id,
                        case_number=monitored_case.case_number,
                        court_id=monitored_case.court_id,
                        change_type=change_type,
                        severity=severity,
                        detected_at=datetime.now(timezone.utc),
                        description=f"New {change_type.value}: {entry.get('description', '')[:100]}",
                        new_value=entry,
                        affected_entry_number=entry.get('entry_number'),
                        metadata={
                            'entry_data': entry,
                            'keywords_matched': self._get_matched_keywords(entry, change_type)
                        }
                    )
                    detections.append(detection)
            
            # Process modified entries
            for mod_entry in analysis.modified_entries:
                detection = ChangeDetection(
                    change_id="",
                    monitor_id=monitored_case.monitor_id,
                    case_number=monitored_case.case_number,
                    court_id=monitored_case.court_id,
                    change_type=ChangeType.NEW_DOCKET_ENTRY,  # Modified entry
                    severity=AlertSeverity.LOW,
                    detected_at=datetime.now(timezone.utc),
                    description=f"Modified entry {mod_entry['entry_number']}: {list(mod_entry['changes'].keys())}",
                    old_value=mod_entry['old_entry'],
                    new_value=mod_entry['new_entry'],
                    affected_entry_number=mod_entry['entry_number'],
                    metadata={'changes': mod_entry['changes']}
                )
                detections.append(detection)
            
            # Process new documents
            for doc in analysis.new_documents:
                detection = ChangeDetection(
                    change_id="",
                    monitor_id=monitored_case.monitor_id,
                    case_number=monitored_case.case_number,
                    court_id=monitored_case.court_id,
                    change_type=ChangeType.NEW_DOCUMENT,
                    severity=AlertSeverity.MEDIUM,
                    detected_at=datetime.now(timezone.utc),
                    description=f"New document available: {doc.get('description', '')[:100]}",
                    new_value=doc,
                    affected_entry_number=doc.get('entry_number'),
                    metadata={'document_info': doc}
                )
                detections.append(detection)
            
            # Process case status changes
            for status_change in analysis.status_changes:
                detection = ChangeDetection(
                    change_id="",
                    monitor_id=monitored_case.monitor_id,
                    case_number=monitored_case.case_number,
                    court_id=monitored_case.court_id,
                    change_type=status_change['change_type'],
                    severity=self._determine_status_change_severity(status_change),
                    detected_at=datetime.now(timezone.utc),
                    description=f"{status_change['field']} changed: {status_change['old_value']} → {status_change['new_value']}",
                    old_value=status_change['old_value'],
                    new_value=status_change['new_value'],
                    metadata={'field': status_change['field']}
                )
                detections.append(detection)
            
            logger.info(f"Generated {len(detections)} change detections")
            
        except Exception as e:
            logger.error(f"Change detection generation failed: {str(e)}")
        
        return detections
    
    def _classify_docket_entry(self, entry: Dict[str, Any]) -> List[ChangeType]:
        """Classify a docket entry to determine change types"""
        
        description = entry.get('description', '').lower()
        change_types = []
        
        # Check for motion-related entries
        if any(keyword in description for keyword in self.motion_keywords):
            change_types.append(ChangeType.MOTION_FILED)
        
        # Check for orders
        if any(keyword in description for keyword in self.order_keywords):
            change_types.append(ChangeType.ORDER_ENTERED)
        
        # Check for judgments
        if any(keyword in description for keyword in self.judgment_keywords):
            change_types.append(ChangeType.JUDGMENT_ENTERED)
        
        # Check for hearings
        if any(keyword in description for keyword in self.hearing_keywords):
            change_types.append(ChangeType.HEARING_SCHEDULED)
        
        # Check for deadlines
        if any(keyword in description for keyword in self.deadline_keywords):
            change_types.append(ChangeType.DEADLINE_CHANGE)
        
        # Default to new docket entry if no specific type identified
        if not change_types:
            change_types.append(ChangeType.NEW_DOCKET_ENTRY)
        
        return change_types
    
    def _determine_severity(self, change_type: ChangeType, entry: Dict[str, Any]) -> AlertSeverity:
        """Determine alert severity based on change type and content"""
        
        description = entry.get('description', '').lower()
        
        # Check for urgent keywords
        if any(keyword in description for keyword in self.urgent_keywords):
            return AlertSeverity.URGENT
        
        # Base severity by change type
        severity_map = {
            ChangeType.JUDGMENT_ENTERED: AlertSeverity.URGENT,
            ChangeType.ORDER_ENTERED: AlertSeverity.CRITICAL,
            ChangeType.MOTION_FILED: AlertSeverity.HIGH,
            ChangeType.HEARING_SCHEDULED: AlertSeverity.HIGH,
            ChangeType.DEADLINE_CHANGE: AlertSeverity.HIGH,
            ChangeType.CASE_CLOSED: AlertSeverity.HIGH,
            ChangeType.CASE_REOPENED: AlertSeverity.HIGH,
            ChangeType.NEW_DOCUMENT: AlertSeverity.MEDIUM,
            ChangeType.NEW_DOCKET_ENTRY: AlertSeverity.MEDIUM,
            ChangeType.PARTY_CHANGE: AlertSeverity.MEDIUM,
            ChangeType.JUDGE_CHANGE: AlertSeverity.MEDIUM,
            ChangeType.CASE_STATUS_CHANGE: AlertSeverity.MEDIUM
        }
        
        base_severity = severity_map.get(change_type, AlertSeverity.LOW)
        
        # Upgrade severity for certain keywords
        high_priority_keywords = [
            "granted", "denied", "dismissed", "summary judgment",
            "preliminary injunction", "contempt", "sanctions"
        ]
        
        if any(keyword in description for keyword in high_priority_keywords):
            if base_severity.value == "low":
                return AlertSeverity.MEDIUM
            elif base_severity.value == "medium":
                return AlertSeverity.HIGH
            elif base_severity.value == "high":
                return AlertSeverity.CRITICAL
        
        return base_severity
    
    def _determine_status_change_severity(self, status_change: Dict[str, Any]) -> AlertSeverity:
        """Determine severity for case status changes"""
        
        field = status_change['field']
        new_value = str(status_change.get('new_value', '')).lower()
        
        if field == 'judge_name':
            return AlertSeverity.MEDIUM
        elif field == 'case_status':
            if 'closed' in new_value or 'dismissed' in new_value:
                return AlertSeverity.HIGH
            else:
                return AlertSeverity.MEDIUM
        elif field == 'parties':
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _get_matched_keywords(
        self, 
        entry: Dict[str, Any], 
        change_type: ChangeType
    ) -> List[str]:
        """Get keywords that matched for this change type"""
        
        description = entry.get('description', '').lower()
        matched = []
        
        keyword_map = {
            ChangeType.MOTION_FILED: self.motion_keywords,
            ChangeType.ORDER_ENTERED: self.order_keywords,
            ChangeType.JUDGMENT_ENTERED: self.judgment_keywords,
            ChangeType.HEARING_SCHEDULED: self.hearing_keywords,
            ChangeType.DEADLINE_CHANGE: self.deadline_keywords
        }
        
        keywords = keyword_map.get(change_type, [])
        
        for keyword in keywords:
            if keyword in description:
                matched.append(keyword)
        
        # Check urgent keywords too
        for keyword in self.urgent_keywords:
            if keyword in description:
                matched.append(f"URGENT:{keyword}")
        
        return matched
    
    def calculate_docket_hash(self, docket_entries: List[Dict[str, Any]]) -> str:
        """Calculate hash of docket entries for change detection"""
        
        try:
            # Create a consistent representation for hashing
            hash_data = []
            
            for entry in docket_entries:
                entry_hash_data = {
                    'entry_number': entry.get('entry_number', ''),
                    'description': entry.get('description', ''),
                    'date_filed': entry.get('date_filed', ''),
                    'document_count': len(entry.get('document_links', []))
                }
                hash_data.append(entry_hash_data)
            
            # Sort by entry number for consistency
            hash_data.sort(key=lambda x: x.get('entry_number', ''))
            
            # Create hash
            hash_string = json.dumps(hash_data, sort_keys=True)
            return hashlib.md5(hash_string.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Hash calculation failed: {str(e)}")
            return ""
    
    def quick_change_check(
        self,
        monitored_case: MonitoredCase,
        current_docket_entries: List[Dict[str, Any]]
    ) -> bool:
        """Quick check if changes exist without full analysis"""
        
        try:
            # Calculate current hash
            current_hash = self.calculate_docket_hash(current_docket_entries)
            
            # Compare with cached hash
            if monitored_case.cached_docket_hash != current_hash:
                logger.debug(f"Hash mismatch detected for case {monitored_case.case_number}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Quick change check failed: {str(e)}")
            return True  # Assume changes if check fails


# Global detector instance
change_detector = ChangeDetector()