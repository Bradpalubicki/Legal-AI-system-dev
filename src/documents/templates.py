"""
Template Library System
Comprehensive template management with court forms, motion templates, and auto-fill capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import asyncio
import json
import re
from pathlib import Path


class TemplateType(str, Enum):
    COURT_FORM = "court_form"
    MOTION = "motion"
    RESPONSE = "response"
    BRIEF = "brief"
    CONTRACT = "contract"
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    NOTICE = "notice"
    CORRESPONDENCE = "correspondence"
    CUSTOM = "custom"


class TemplateCategory(str, Enum):
    CIVIL_LITIGATION = "civil_litigation"
    CRIMINAL_DEFENSE = "criminal_defense"
    FAMILY_LAW = "family_law"
    CORPORATE = "corporate"
    REAL_ESTATE = "real_estate"
    EMPLOYMENT = "employment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    BANKRUPTCY = "bankruptcy"
    IMMIGRATION = "immigration"
    PERSONAL_INJURY = "personal_injury"
    GENERAL = "general"


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SIGNATURE = "signature"
    CALCULATED = "calculated"


class ValidationRule(str, Enum):
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    RANGE = "range"
    UNIQUE = "unique"
    CUSTOM = "custom"


class JurisdictionLevel(str, Enum):
    FEDERAL = "federal"
    STATE = "state"
    COUNTY = "county"
    CITY = "city"
    TRIBAL = "tribal"


@dataclass
class TemplateField:
    field_id: str
    name: str
    field_type: FieldType
    label: str
    description: str
    required: bool = False
    default_value: Optional[str] = None
    placeholder: str = ""
    choices: List[str] = field(default_factory=list)
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conditional_logic: Optional[Dict[str, Any]] = None
    auto_populate_source: Optional[str] = None
    formatting_rules: Dict[str, Any] = field(default_factory=dict)
    help_text: str = ""


@dataclass
class TemplateSection:
    section_id: str
    title: str
    description: str
    fields: List[TemplateField]
    order: int = 0
    collapsible: bool = True
    conditional_display: Optional[Dict[str, Any]] = None
    template_content: str = ""
    formatting_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Template:
    template_id: str
    name: str
    description: str
    template_type: TemplateType
    category: TemplateCategory
    jurisdiction: str
    jurisdiction_level: JurisdictionLevel
    sections: List[TemplateSection]
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: str = "1.0"
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_format: str = "docx"
    preview_image: Optional[str] = None
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TemplateInstance:
    instance_id: str
    template_id: str
    created_by: str
    created_at: datetime
    field_values: Dict[str, Any]
    status: str = "draft"
    completed_at: Optional[datetime] = None
    generated_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoFillMapping:
    mapping_id: str
    name: str
    description: str
    source_system: str
    field_mappings: Dict[str, str]
    transformation_rules: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TemplateLibrary:
    library_id: str
    name: str
    description: str
    templates: List[str]  # Template IDs
    created_by: str
    created_at: datetime
    is_public: bool = False
    access_permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplateManager:
    def __init__(self):
        self.templates = {}
        self.instances = {}
        self.libraries = {}
        self.auto_fill_mappings = {}
        self.user_data_cache = {}

    async def create_template(self, template: Template) -> bool:
        """Create a new template"""
        try:
            self.templates[template.template_id] = template
            print(f"Created template: {template.name}")
            return True
        except Exception as e:
            print(f"Error creating template: {e}")
            return False

    async def initialize_default_templates(self) -> bool:
        """Initialize default court forms and common templates"""
        try:
            # Civil Motion Template
            civil_motion = Template(
                template_id="civil_motion_001",
                name="Motion for Summary Judgment",
                description="Standard motion for summary judgment in civil litigation",
                template_type=TemplateType.MOTION,
                category=TemplateCategory.CIVIL_LITIGATION,
                jurisdiction="Federal",
                jurisdiction_level=JurisdictionLevel.FEDERAL,
                sections=[
                    TemplateSection(
                        section_id="case_info",
                        title="Case Information",
                        description="Basic case details",
                        order=1,
                        fields=[
                            TemplateField(
                                field_id="case_number",
                                name="case_number",
                                field_type=FieldType.TEXT,
                                label="Case Number",
                                description="Court case number",
                                required=True,
                                validation_rules=[{"rule": "required", "message": "Case number is required"}]
                            ),
                            TemplateField(
                                field_id="court_name",
                                name="court_name",
                                field_type=FieldType.TEXT,
                                label="Court Name",
                                description="Name of the court",
                                required=True,
                                placeholder="U.S. District Court for the..."
                            ),
                            TemplateField(
                                field_id="judge_name",
                                name="judge_name",
                                field_type=FieldType.TEXT,
                                label="Judge Name",
                                description="Presiding judge",
                                required=False,
                                placeholder="The Honorable..."
                            )
                        ],
                        template_content="IN THE {court_name}\nCASE NO. {case_number}\nJUDGE: {judge_name}"
                    ),
                    TemplateSection(
                        section_id="parties",
                        title="Party Information",
                        description="Plaintiff and defendant information",
                        order=2,
                        fields=[
                            TemplateField(
                                field_id="plaintiff_name",
                                name="plaintiff_name",
                                field_type=FieldType.TEXT,
                                label="Plaintiff Name",
                                description="Name of plaintiff",
                                required=True
                            ),
                            TemplateField(
                                field_id="defendant_name",
                                name="defendant_name",
                                field_type=FieldType.TEXT,
                                label="Defendant Name",
                                description="Name of defendant",
                                required=True
                            )
                        ],
                        template_content="{plaintiff_name},\n\tv.\n{defendant_name}"
                    ),
                    TemplateSection(
                        section_id="motion_details",
                        title="Motion Details",
                        description="Specific motion information",
                        order=3,
                        fields=[
                            TemplateField(
                                field_id="motion_title",
                                name="motion_title",
                                field_type=FieldType.TEXT,
                                label="Motion Title",
                                description="Title of the motion",
                                required=True,
                                default_value="Motion for Summary Judgment"
                            ),
                            TemplateField(
                                field_id="grounds",
                                name="grounds",
                                field_type=FieldType.TEXT,
                                label="Grounds for Motion",
                                description="Legal grounds for the motion",
                                required=True
                            ),
                            TemplateField(
                                field_id="relief_sought",
                                name="relief_sought",
                                field_type=FieldType.TEXT,
                                label="Relief Sought",
                                description="What you are asking the court to do",
                                required=True
                            )
                        ],
                        template_content="MOTION FOR {motion_title}\n\nTO THE HONORABLE COURT:\n\nComes now {plaintiff_name}, through counsel, and respectfully moves this Court for {relief_sought} on the following grounds:\n\n{grounds}"
                    )
                ],
                created_by="system",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=["motion", "summary judgment", "civil", "federal"]
            )

            # Discovery Request Template
            discovery_template = Template(
                template_id="discovery_001",
                name="Request for Production of Documents",
                description="Standard document production request",
                template_type=TemplateType.DISCOVERY,
                category=TemplateCategory.CIVIL_LITIGATION,
                jurisdiction="General",
                jurisdiction_level=JurisdictionLevel.STATE,
                sections=[
                    TemplateSection(
                        section_id="intro",
                        title="Introduction",
                        description="Opening information",
                        order=1,
                        fields=[
                            TemplateField(
                                field_id="requesting_party",
                                name="requesting_party",
                                field_type=FieldType.TEXT,
                                label="Requesting Party",
                                description="Party making the request",
                                required=True
                            ),
                            TemplateField(
                                field_id="responding_party",
                                name="responding_party",
                                field_type=FieldType.TEXT,
                                label="Responding Party",
                                description="Party who must respond",
                                required=True
                            ),
                            TemplateField(
                                field_id="response_deadline",
                                name="response_deadline",
                                field_type=FieldType.DATE,
                                label="Response Deadline",
                                description="Date response is due",
                                required=True
                            )
                        ],
                        template_content="TO: {responding_party}\n\nYou are requested to produce the following documents within {response_deadline} days of service of this request."
                    ),
                    TemplateSection(
                        section_id="requests",
                        title="Document Requests",
                        description="Specific document requests",
                        order=2,
                        fields=[
                            TemplateField(
                                field_id="document_categories",
                                name="document_categories",
                                field_type=FieldType.MULTI_CHOICE,
                                label="Document Categories",
                                description="Types of documents requested",
                                choices=[
                                    "All contracts and agreements",
                                    "Financial records and statements",
                                    "Email communications",
                                    "Meeting minutes and notes",
                                    "Reports and analyses",
                                    "Personnel files",
                                    "Other (specify)"
                                ]
                            )
                        ]
                    )
                ],
                created_by="system",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=["discovery", "production", "documents"]
            )

            # Contract Template
            contract_template = Template(
                template_id="contract_001",
                name="Service Agreement",
                description="Standard service agreement contract",
                template_type=TemplateType.CONTRACT,
                category=TemplateCategory.CORPORATE,
                jurisdiction="General",
                jurisdiction_level=JurisdictionLevel.STATE,
                sections=[
                    TemplateSection(
                        section_id="parties",
                        title="Parties",
                        description="Contract parties",
                        order=1,
                        fields=[
                            TemplateField(
                                field_id="client_name",
                                name="client_name",
                                field_type=FieldType.TEXT,
                                label="Client Name",
                                description="Name of the client",
                                required=True
                            ),
                            TemplateField(
                                field_id="client_address",
                                name="client_address",
                                field_type=FieldType.ADDRESS,
                                label="Client Address",
                                description="Client's address",
                                required=True
                            ),
                            TemplateField(
                                field_id="service_provider",
                                name="service_provider",
                                field_type=FieldType.TEXT,
                                label="Service Provider",
                                description="Name of service provider",
                                required=True
                            ),
                            TemplateField(
                                field_id="effective_date",
                                name="effective_date",
                                field_type=FieldType.DATE,
                                label="Effective Date",
                                description="Contract start date",
                                required=True
                            ),
                            TemplateField(
                                field_id="term_length",
                                name="term_length",
                                field_type=FieldType.CHOICE,
                                label="Contract Term",
                                description="Length of contract",
                                choices=["6 months", "1 year", "2 years", "3 years", "Other"],
                                required=True
                            )
                        ]
                    )
                ],
                created_by="system",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=["contract", "service", "agreement"]
            )

            # Store templates
            await self.create_template(civil_motion)
            await self.create_template(discovery_template)
            await self.create_template(contract_template)

            # Create auto-fill mappings
            await self.create_auto_fill_mapping(AutoFillMapping(
                mapping_id="client_data_mapping",
                name="Client Data Auto-Fill",
                description="Auto-fill client information from CRM",
                source_system="CRM",
                field_mappings={
                    "client_name": "contact.full_name",
                    "client_address": "contact.address",
                    "client_email": "contact.email",
                    "client_phone": "contact.phone"
                }
            ))

            return True

        except Exception as e:
            print(f"Error initializing default templates: {e}")
            return False

    async def get_templates(self, category: Optional[TemplateCategory] = None,
                           template_type: Optional[TemplateType] = None,
                           jurisdiction: Optional[str] = None) -> List[Template]:
        """Get templates with optional filtering"""
        try:
            templates = list(self.templates.values())

            if category:
                templates = [t for t in templates if t.category == category]

            if template_type:
                templates = [t for t in templates if t.template_type == template_type]

            if jurisdiction:
                templates = [t for t in templates if t.jurisdiction.lower() == jurisdiction.lower()]

            return sorted(templates, key=lambda x: (x.usage_count, x.rating), reverse=True)

        except Exception as e:
            print(f"Error getting templates: {e}")
            return []

    async def create_instance(self, template_id: str, user_id: str,
                            initial_values: Optional[Dict[str, Any]] = None) -> Optional[TemplateInstance]:
        """Create an instance of a template"""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError("Template not found")

            instance_id = f"instance_{len(self.instances) + 1}"

            # Initialize field values
            field_values = initial_values or {}

            # Apply auto-fill mappings
            if user_id in self.user_data_cache:
                user_data = self.user_data_cache[user_id]
                field_values.update(await self._apply_auto_fill(template, user_data))

            instance = TemplateInstance(
                instance_id=instance_id,
                template_id=template_id,
                created_by=user_id,
                created_at=datetime.utcnow(),
                field_values=field_values
            )

            self.instances[instance_id] = instance

            # Increment usage count
            template.usage_count += 1

            return instance

        except Exception as e:
            print(f"Error creating template instance: {e}")
            return None

    async def _apply_auto_fill(self, template: Template, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply auto-fill mappings to template fields"""
        try:
            filled_values = {}

            for section in template.sections:
                for field in section.fields:
                    if field.auto_populate_source:
                        # Simple path-based data extraction
                        value = self._extract_value_by_path(user_data, field.auto_populate_source)
                        if value:
                            filled_values[field.field_id] = value

            # Apply global mappings
            for mapping in self.auto_fill_mappings.values():
                if mapping.is_active:
                    for field_id, source_path in mapping.field_mappings.items():
                        if field_id not in filled_values:
                            value = self._extract_value_by_path(user_data, source_path)
                            if value:
                                filled_values[field_id] = value

            return filled_values

        except Exception as e:
            print(f"Error applying auto-fill: {e}")
            return {}

    def _extract_value_by_path(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        """Extract value from nested dictionary using dot notation"""
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except Exception:
            return None

    async def update_instance_values(self, instance_id: str,
                                   field_values: Dict[str, Any]) -> bool:
        """Update field values in a template instance"""
        try:
            instance = self.instances.get(instance_id)
            if not instance:
                return False

            # Validate values against template
            template = self.templates.get(instance.template_id)
            if template:
                validation_errors = await self._validate_field_values(template, field_values)
                if validation_errors:
                    print(f"Validation errors: {validation_errors}")
                    return False

            instance.field_values.update(field_values)
            return True

        except Exception as e:
            print(f"Error updating instance values: {e}")
            return False

    async def _validate_field_values(self, template: Template,
                                   field_values: Dict[str, Any]) -> List[str]:
        """Validate field values against template rules"""
        errors = []

        try:
            # Create field lookup
            all_fields = {}
            for section in template.sections:
                for field in section.fields:
                    all_fields[field.field_id] = field

            # Validate each field
            for field_id, value in field_values.items():
                field = all_fields.get(field_id)
                if not field:
                    continue

                # Required field validation
                if field.required and (value is None or value == ""):
                    errors.append(f"{field.label} is required")

                # Type validation
                if value and not self._validate_field_type(field, value):
                    errors.append(f"{field.label} has invalid format")

                # Custom validation rules
                for rule in field.validation_rules:
                    if not self._validate_rule(rule, value):
                        errors.append(rule.get("message", f"{field.label} validation failed"))

            return errors

        except Exception as e:
            print(f"Error validating field values: {e}")
            return ["Validation error occurred"]

    def _validate_field_type(self, field: TemplateField, value: Any) -> bool:
        """Validate value type against field type"""
        try:
            if field.field_type == FieldType.EMAIL:
                return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)) is not None
            elif field.field_type == FieldType.PHONE:
                return re.match(r'^\+?[\d\s\-\(\)]{10,}$', str(value)) is not None
            elif field.field_type == FieldType.DATE:
                # Would implement proper date validation
                return True
            elif field.field_type == FieldType.NUMBER:
                try:
                    float(value)
                    return True
                except:
                    return False
            else:
                return True
        except:
            return False

    def _validate_rule(self, rule: Dict[str, Any], value: Any) -> bool:
        """Validate value against a specific rule"""
        try:
            rule_type = rule.get("rule")

            if rule_type == "min_length":
                return len(str(value)) >= rule.get("value", 0)
            elif rule_type == "max_length":
                return len(str(value)) <= rule.get("value", float('inf'))
            elif rule_type == "pattern":
                pattern = rule.get("value", ".*")
                return re.match(pattern, str(value)) is not None
            else:
                return True
        except:
            return False

    async def generate_document(self, instance_id: str) -> Optional[str]:
        """Generate document content from template instance"""
        try:
            instance = self.instances.get(instance_id)
            if not instance:
                return None

            template = self.templates.get(instance.template_id)
            if not template:
                return None

            # Build complete document
            document_content = []

            for section in sorted(template.sections, key=lambda x: x.order):
                if section.template_content:
                    # Replace placeholders with actual values
                    content = section.template_content
                    for field_id, value in instance.field_values.items():
                        placeholder = "{" + field_id + "}"
                        if placeholder in content:
                            content = content.replace(placeholder, str(value))

                    document_content.append(content)

            generated_content = "\n\n".join(document_content)

            # Store generated content
            instance.generated_content = generated_content
            instance.status = "completed"
            instance.completed_at = datetime.utcnow()

            return generated_content

        except Exception as e:
            print(f"Error generating document: {e}")
            return None

    async def create_auto_fill_mapping(self, mapping: AutoFillMapping) -> bool:
        """Create auto-fill mapping"""
        try:
            self.auto_fill_mappings[mapping.mapping_id] = mapping
            return True
        except Exception as e:
            print(f"Error creating auto-fill mapping: {e}")
            return False

    async def search_templates(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Template]:
        """Search templates by name, description, tags"""
        try:
            results = []
            query_lower = query.lower()

            for template in self.templates.values():
                # Search in name, description, tags
                if (query_lower in template.name.lower() or
                    query_lower in template.description.lower() or
                    any(query_lower in tag.lower() for tag in template.tags)):
                    results.append(template)

            # Apply additional filters
            if filters:
                if "category" in filters:
                    results = [t for t in results if t.category == filters["category"]]
                if "type" in filters:
                    results = [t for t in results if t.template_type == filters["type"]]
                if "jurisdiction" in filters:
                    results = [t for t in results if filters["jurisdiction"].lower() in t.jurisdiction.lower()]

            return sorted(results, key=lambda x: x.usage_count, reverse=True)

        except Exception as e:
            print(f"Error searching templates: {e}")
            return []

    async def create_custom_template(self, name: str, description: str,
                                   template_type: TemplateType, category: TemplateCategory,
                                   sections: List[TemplateSection], user_id: str) -> Optional[Template]:
        """Create a custom template"""
        try:
            template_id = f"custom_{len([t for t in self.templates.values() if t.created_by != 'system']) + 1}"

            template = Template(
                template_id=template_id,
                name=name,
                description=description,
                template_type=template_type,
                category=category,
                jurisdiction="General",
                jurisdiction_level=JurisdictionLevel.STATE,
                sections=sections,
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=["custom"]
            )

            await self.create_template(template)
            return template

        except Exception as e:
            print(f"Error creating custom template: {e}")
            return None

    async def get_template_analytics(self, template_id: str) -> Dict[str, Any]:
        """Get analytics for a specific template"""
        try:
            template = self.templates.get(template_id)
            if not template:
                return {}

            instances = [i for i in self.instances.values() if i.template_id == template_id]

            return {
                "template_id": template_id,
                "name": template.name,
                "usage_count": template.usage_count,
                "total_instances": len(instances),
                "completed_instances": len([i for i in instances if i.status == "completed"]),
                "average_completion_time": self._calculate_avg_completion_time(instances),
                "most_common_values": self._analyze_common_field_values(instances),
                "user_ratings": {
                    "average": template.rating,
                    "total_reviews": len(template.reviews)
                }
            }

        except Exception as e:
            print(f"Error getting template analytics: {e}")
            return {}

    def _calculate_avg_completion_time(self, instances: List[TemplateInstance]) -> float:
        """Calculate average completion time for instances"""
        completed_instances = [i for i in instances if i.completed_at and i.created_at]
        if not completed_instances:
            return 0.0

        total_time = sum(
            (i.completed_at - i.created_at).total_seconds()
            for i in completed_instances
        )

        return total_time / len(completed_instances) / 60  # Return in minutes

    def _analyze_common_field_values(self, instances: List[TemplateInstance]) -> Dict[str, Any]:
        """Analyze most common field values"""
        field_usage = {}

        for instance in instances:
            for field_id, value in instance.field_values.items():
                if field_id not in field_usage:
                    field_usage[field_id] = {}

                value_str = str(value)
                if value_str not in field_usage[field_id]:
                    field_usage[field_id][value_str] = 0
                field_usage[field_id][value_str] += 1

        # Get most common value for each field
        common_values = {}
        for field_id, values in field_usage.items():
            if values:
                most_common = max(values, key=values.get)
                common_values[field_id] = {
                    "value": most_common,
                    "usage_count": values[most_common]
                }

        return common_values

    async def get_user_templates(self, user_id: str) -> List[Template]:
        """Get templates created by a specific user"""
        try:
            return [t for t in self.templates.values() if t.created_by == user_id]
        except Exception as e:
            print(f"Error getting user templates: {e}")
            return []

    async def get_template_summary(self) -> Dict[str, Any]:
        """Get summary of template system"""
        try:
            return {
                "total_templates": len(self.templates),
                "total_instances": len(self.instances),
                "templates_by_category": self._count_by_category(),
                "templates_by_type": self._count_by_type(),
                "most_popular_templates": self._get_most_popular_templates(),
                "recent_instances": self._get_recent_instances(),
                "auto_fill_mappings": len(self.auto_fill_mappings)
            }
        except Exception as e:
            print(f"Error getting template summary: {e}")
            return {}

    def _count_by_category(self) -> Dict[str, int]:
        """Count templates by category"""
        categories = {}
        for template in self.templates.values():
            category = template.category.value
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _count_by_type(self) -> Dict[str, int]:
        """Count templates by type"""
        types = {}
        for template in self.templates.values():
            template_type = template.template_type.value
            types[template_type] = types.get(template_type, 0) + 1
        return types

    def _get_most_popular_templates(self) -> List[Dict[str, Any]]:
        """Get most popular templates"""
        sorted_templates = sorted(
            self.templates.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:5]

        return [{
            "template_id": t.template_id,
            "name": t.name,
            "usage_count": t.usage_count,
            "rating": t.rating
        } for t in sorted_templates]

    def _get_recent_instances(self) -> List[Dict[str, Any]]:
        """Get recent template instances"""
        sorted_instances = sorted(
            self.instances.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:5]

        return [{
            "instance_id": i.instance_id,
            "template_id": i.template_id,
            "created_at": i.created_at.isoformat(),
            "status": i.status
        } for i in sorted_instances]


# Global instance
template_manager = TemplateManager()


# FastAPI endpoints configuration
async def get_template_endpoints():
    """Return FastAPI endpoint configurations for template system"""
    return [
        {
            "path": "/templates",
            "method": "GET",
            "handler": "get_templates",
            "description": "Get available templates"
        },
        {
            "path": "/templates/search",
            "method": "GET",
            "handler": "search_templates",
            "description": "Search templates"
        },
        {
            "path": "/templates",
            "method": "POST",
            "handler": "create_custom_template",
            "description": "Create custom template"
        },
        {
            "path": "/templates/{template_id}",
            "method": "GET",
            "handler": "get_template_details",
            "description": "Get template details"
        },
        {
            "path": "/templates/{template_id}/analytics",
            "method": "GET",
            "handler": "get_template_analytics",
            "description": "Get template analytics"
        },
        {
            "path": "/templates/{template_id}/instances",
            "method": "POST",
            "handler": "create_template_instance",
            "description": "Create template instance"
        },
        {
            "path": "/templates/instances/{instance_id}",
            "method": "PUT",
            "handler": "update_template_instance",
            "description": "Update template instance"
        },
        {
            "path": "/templates/instances/{instance_id}/generate",
            "method": "POST",
            "handler": "generate_document_from_template",
            "description": "Generate document from template"
        },
        {
            "path": "/templates/auto-fill",
            "method": "POST",
            "handler": "create_auto_fill_mapping",
            "description": "Create auto-fill mapping"
        },
        {
            "path": "/templates/summary",
            "method": "GET",
            "handler": "get_template_system_summary",
            "description": "Get template system summary"
        }
    ]


async def initialize_template_system():
    """Initialize the template system"""
    try:
        # Initialize default templates
        await template_manager.initialize_default_templates()

        print("Template Library System initialized successfully")
        print(f"Available endpoints: {len(await get_template_endpoints())}")
        print(f"Default templates created: {len(template_manager.templates)}")
        return True
    except Exception as e:
        print(f"Error initializing template system: {e}")
        return False