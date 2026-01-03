"""
White-Label Customization System
Comprehensive branding and customization capabilities for law firms.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field, validator
import json
import uuid
import os
import shutil
from pathlib import Path
import re
from PIL import Image
import base64
from io import BytesIO


class BrandingTheme(Enum):
    PROFESSIONAL = "professional"
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CUSTOM = "custom"


class LanguageCode(Enum):
    EN_US = "en-US"
    EN_GB = "en-GB"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    IT_IT = "it-IT"
    PT_BR = "pt-BR"
    ZH_CN = "zh-CN"
    JA_JP = "ja-JP"


class ModulePermission(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    VIEW_ONLY = "view_only"
    LIMITED = "limited"


@dataclass
class ColorScheme:
    primary: str = "#1f2937"           # Dark gray
    secondary: str = "#3b82f6"         # Blue
    accent: str = "#10b981"            # Green
    background: str = "#ffffff"        # White
    surface: str = "#f9fafb"          # Light gray
    text_primary: str = "#111827"      # Dark
    text_secondary: str = "#6b7280"    # Gray
    error: str = "#ef4444"            # Red
    warning: str = "#f59e0b"          # Amber
    success: str = "#10b981"          # Green


@dataclass
class Typography:
    font_family_primary: str = "Inter, sans-serif"
    font_family_secondary: str = "Georgia, serif"
    font_size_base: str = "16px"
    font_size_small: str = "14px"
    font_size_large: str = "18px"
    font_size_xl: str = "24px"
    font_weight_normal: str = "400"
    font_weight_medium: str = "500"
    font_weight_bold: str = "700"
    line_height: str = "1.5"


@dataclass
class LogoConfiguration:
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None  # For dark themes
    favicon_url: Optional[str] = None
    watermark_url: Optional[str] = None
    max_width: str = "200px"
    max_height: str = "80px"
    background_transparent: bool = True


@dataclass
class EmailTemplateConfig:
    header_logo: bool = True
    footer_signature: Optional[str] = None
    color_scheme: bool = True
    custom_templates: Dict[str, str] = field(default_factory=dict)
    sender_name: Optional[str] = None
    reply_to: Optional[str] = None


@dataclass
class DomainConfiguration:
    custom_domain: Optional[str] = None
    subdomain: Optional[str] = None  # firm.legalai.com
    ssl_certificate: Optional[str] = None
    redirect_www: bool = True
    force_https: bool = True


@dataclass
class ModuleConfiguration:
    document_analysis: ModulePermission = ModulePermission.ENABLED
    legal_research: ModulePermission = ModulePermission.ENABLED
    case_management: ModulePermission = ModulePermission.ENABLED
    client_portal: ModulePermission = ModulePermission.ENABLED
    billing_integration: ModulePermission = ModulePermission.ENABLED
    compliance_tools: ModulePermission = ModulePermission.ENABLED
    reporting: ModulePermission = ModulePermission.ENABLED
    api_access: ModulePermission = ModulePermission.DISABLED
    custom_workflows: ModulePermission = ModulePermission.ENABLED
    analytics: ModulePermission = ModulePermission.ENABLED


@dataclass
class PracticeAreaConfiguration:
    primary_areas: List[str] = field(default_factory=list)
    secondary_areas: List[str] = field(default_factory=list)
    custom_areas: List[str] = field(default_factory=list)
    specialized_features: Dict[str, List[str]] = field(default_factory=dict)
    document_templates: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class LocalizationConfiguration:
    primary_language: LanguageCode = LanguageCode.EN_US
    supported_languages: List[LanguageCode] = field(default_factory=lambda: [LanguageCode.EN_US])
    date_format: str = "MM/dd/yyyy"
    time_format: str = "12"  # 12 or 24 hour
    currency: str = "USD"
    timezone: str = "America/New_York"
    number_format: str = "en-US"


@dataclass
class WhiteLabelConfiguration:
    firm_id: str
    firm_name: str
    branding_theme: BrandingTheme = BrandingTheme.PROFESSIONAL
    color_scheme: ColorScheme = field(default_factory=ColorScheme)
    typography: Typography = field(default_factory=Typography)
    logo_config: LogoConfiguration = field(default_factory=LogoConfiguration)
    email_templates: EmailTemplateConfig = field(default_factory=EmailTemplateConfig)
    domain_config: DomainConfiguration = field(default_factory=DomainConfiguration)
    module_config: ModuleConfiguration = field(default_factory=ModuleConfiguration)
    practice_areas: PracticeAreaConfiguration = field(default_factory=PracticeAreaConfiguration)
    localization: LocalizationConfiguration = field(default_factory=LocalizationConfiguration)
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    custom_footer: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


class WhiteLabelCustomizer:
    """Advanced white-label customization system"""

    def __init__(self, storage_path: str = "./storage/whitelabel"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.configurations: Dict[str, WhiteLabelConfiguration] = {}
        self.theme_presets = self._initialize_theme_presets()
        self.practice_area_templates = self._initialize_practice_area_templates()

    def _initialize_theme_presets(self) -> Dict[BrandingTheme, Dict]:
        """Initialize predefined theme presets"""
        return {
            BrandingTheme.PROFESSIONAL: {
                "color_scheme": ColorScheme(
                    primary="#1e293b",
                    secondary="#3b82f6",
                    accent="#0ea5e9",
                    background="#ffffff",
                    surface="#f8fafc",
                    text_primary="#0f172a",
                    text_secondary="#475569"
                ),
                "typography": Typography(
                    font_family_primary="Inter, system-ui, sans-serif",
                    font_family_secondary="Georgia, serif"
                )
            },
            BrandingTheme.MODERN: {
                "color_scheme": ColorScheme(
                    primary="#111827",
                    secondary="#6366f1",
                    accent="#8b5cf6",
                    background="#ffffff",
                    surface="#f9fafb",
                    text_primary="#111827",
                    text_secondary="#4b5563"
                ),
                "typography": Typography(
                    font_family_primary="'SF Pro Display', -apple-system, sans-serif",
                    font_family_secondary="'SF Pro Text', sans-serif"
                )
            },
            BrandingTheme.CLASSIC: {
                "color_scheme": ColorScheme(
                    primary="#7c2d12",
                    secondary="#dc2626",
                    accent="#b91c1c",
                    background="#fffbeb",
                    surface="#fef3c7",
                    text_primary="#451a03",
                    text_secondary="#78350f"
                ),
                "typography": Typography(
                    font_family_primary="Georgia, 'Times New Roman', serif",
                    font_family_secondary="'Crimson Text', serif"
                )
            },
            BrandingTheme.MINIMAL: {
                "color_scheme": ColorScheme(
                    primary="#000000",
                    secondary="#404040",
                    accent="#737373",
                    background="#ffffff",
                    surface="#fafafa",
                    text_primary="#000000",
                    text_secondary="#525252"
                ),
                "typography": Typography(
                    font_family_primary="'Helvetica Neue', Arial, sans-serif",
                    font_size_base="15px",
                    line_height="1.6"
                )
            },
            BrandingTheme.CORPORATE: {
                "color_scheme": ColorScheme(
                    primary="#1e40af",
                    secondary="#059669",
                    accent="#dc2626",
                    background="#ffffff",
                    surface="#f0f9ff",
                    text_primary="#1e3a8a",
                    text_secondary="#1e40af"
                ),
                "typography": Typography(
                    font_family_primary="'Segoe UI', Tahoma, sans-serif",
                    font_family_secondary="'Times New Roman', serif"
                )
            }
        }

    def _initialize_practice_area_templates(self) -> Dict[str, Dict]:
        """Initialize practice area specific templates"""
        return {
            "litigation": {
                "specialized_features": [
                    "case_timeline", "discovery_management", "court_filing_tracker",
                    "witness_management", "evidence_repository"
                ],
                "document_templates": [
                    "motion_to_dismiss", "discovery_request", "deposition_notice",
                    "settlement_agreement", "trial_brief"
                ],
                "color_accent": "#dc2626"  # Red for urgency
            },
            "corporate": {
                "specialized_features": [
                    "contract_lifecycle", "compliance_tracking", "board_resolutions",
                    "merger_acquisition_tools", "regulatory_filings"
                ],
                "document_templates": [
                    "service_agreement", "nda", "employment_contract",
                    "board_resolution", "stock_purchase_agreement"
                ],
                "color_accent": "#059669"  # Green for growth
            },
            "real_estate": {
                "specialized_features": [
                    "closing_checklist", "title_search", "property_analysis",
                    "lease_management", "zoning_compliance"
                ],
                "document_templates": [
                    "purchase_agreement", "lease_agreement", "deed",
                    "title_opinion", "closing_statement"
                ],
                "color_accent": "#d97706"  # Orange for property
            },
            "family_law": {
                "specialized_features": [
                    "custody_calculator", "asset_division", "mediation_tools",
                    "child_support_tracker", "visitation_scheduler"
                ],
                "document_templates": [
                    "divorce_petition", "custody_agreement", "prenuptial_agreement",
                    "separation_agreement", "child_support_order"
                ],
                "color_accent": "#7c3aed"  # Purple for sensitivity
            },
            "immigration": {
                "specialized_features": [
                    "visa_tracker", "case_status_monitor", "document_checklist",
                    "deadline_calendar", "client_portal"
                ],
                "document_templates": [
                    "i130_petition", "i485_application", "asylum_application",
                    "naturalization_form", "work_permit_renewal"
                ],
                "color_accent": "#0ea5e9"  # Blue for international
            }
        }

    async def create_configuration(
        self,
        firm_id: str,
        firm_name: str,
        initial_theme: BrandingTheme = BrandingTheme.PROFESSIONAL
    ) -> WhiteLabelConfiguration:
        """Create new white-label configuration"""

        # Apply theme preset
        theme_preset = self.theme_presets.get(initial_theme, {})

        config = WhiteLabelConfiguration(
            firm_id=firm_id,
            firm_name=firm_name,
            branding_theme=initial_theme
        )

        # Apply theme-specific defaults
        if "color_scheme" in theme_preset:
            config.color_scheme = theme_preset["color_scheme"]
        if "typography" in theme_preset:
            config.typography = theme_preset["typography"]

        # Set up subdomain
        config.domain_config.subdomain = self._generate_subdomain(firm_name)

        # Default email configuration
        config.email_templates.sender_name = firm_name
        config.email_templates.reply_to = f"noreply@{config.domain_config.subdomain}.legalai.com"

        self.configurations[firm_id] = config
        await self._save_configuration(config)

        return config

    def _generate_subdomain(self, firm_name: str) -> str:
        """Generate a subdomain from firm name"""
        # Clean and format firm name for subdomain
        subdomain = re.sub(r'[^a-zA-Z0-9\s]', '', firm_name.lower())
        subdomain = re.sub(r'\s+', '-', subdomain)
        subdomain = subdomain.strip('-')

        # Ensure it's not too long
        if len(subdomain) > 30:
            subdomain = subdomain[:30].rstrip('-')

        return subdomain

    async def update_branding(
        self,
        firm_id: str,
        color_scheme: Optional[ColorScheme] = None,
        typography: Optional[Typography] = None,
        theme: Optional[BrandingTheme] = None
    ) -> WhiteLabelConfiguration:
        """Update branding configuration"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]

        if theme and theme != config.branding_theme:
            # Apply new theme preset
            theme_preset = self.theme_presets.get(theme, {})
            config.branding_theme = theme

            if "color_scheme" in theme_preset:
                config.color_scheme = theme_preset["color_scheme"]
            if "typography" in theme_preset:
                config.typography = theme_preset["typography"]

        if color_scheme:
            config.color_scheme = color_scheme

        if typography:
            config.typography = typography

        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return config

    async def upload_logo(
        self,
        firm_id: str,
        logo_file: UploadFile,
        logo_type: str = "primary"  # primary, dark, favicon, watermark
    ) -> str:
        """Upload and process logo files"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/svg+xml"]
        if logo_file.content_type not in allowed_types:
            raise ValueError(f"Unsupported file type: {logo_file.content_type}")

        # Create firm-specific directory
        firm_dir = self.storage_path / firm_id / "logos"
        firm_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        file_extension = logo_file.filename.split('.')[-1]
        filename = f"{logo_type}.{file_extension}"
        file_path = firm_dir / filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo_file.file, buffer)

        # Process image (resize if needed)
        if logo_file.content_type != "image/svg+xml":
            await self._process_logo_image(file_path, logo_type)

        # Update configuration
        config = self.configurations[firm_id]
        logo_url = f"/whitelabel/{firm_id}/logos/{filename}"

        if logo_type == "primary":
            config.logo_config.logo_url = logo_url
        elif logo_type == "dark":
            config.logo_config.logo_dark_url = logo_url
        elif logo_type == "favicon":
            config.logo_config.favicon_url = logo_url
        elif logo_type == "watermark":
            config.logo_config.watermark_url = logo_url

        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return logo_url

    async def _process_logo_image(self, file_path: Path, logo_type: str):
        """Process and optimize logo images"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB' and img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Resize based on logo type
                if logo_type == "primary":
                    max_size = (400, 160)  # 2x for retina
                elif logo_type == "favicon":
                    max_size = (64, 64)
                elif logo_type == "watermark":
                    max_size = (200, 200)
                else:
                    max_size = (400, 160)

                # Resize maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save optimized version
                img.save(file_path, optimize=True, quality=85)

        except Exception as e:
            print(f"Error processing logo: {e}")

    async def configure_practice_areas(
        self,
        firm_id: str,
        primary_areas: List[str],
        custom_features: Dict[str, Any] = None
    ) -> WhiteLabelConfiguration:
        """Configure practice area specialization"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]
        config.practice_areas.primary_areas = primary_areas

        # Apply practice area templates
        for area in primary_areas:
            if area in self.practice_area_templates:
                template = self.practice_area_templates[area]

                # Add specialized features
                if "specialized_features" in template:
                    config.practice_areas.specialized_features[area] = template["specialized_features"]

                # Add document templates
                if "document_templates" in template:
                    config.practice_areas.document_templates[area] = template["document_templates"]

                # Optionally adjust color scheme for primary practice area
                if area == primary_areas[0] and "color_accent" in template:
                    config.color_scheme.accent = template["color_accent"]

        # Apply custom features
        if custom_features:
            for area, features in custom_features.items():
                if isinstance(features, list):
                    config.practice_areas.specialized_features[area] = features

        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return config

    async def configure_modules(
        self,
        firm_id: str,
        module_permissions: Dict[str, ModulePermission]
    ) -> WhiteLabelConfiguration:
        """Configure module access and permissions"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]

        # Update module configurations
        for module_name, permission in module_permissions.items():
            if hasattr(config.module_config, module_name):
                setattr(config.module_config, module_name, permission)

        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return config

    async def configure_localization(
        self,
        firm_id: str,
        localization: LocalizationConfiguration
    ) -> WhiteLabelConfiguration:
        """Configure localization settings"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]
        config.localization = localization
        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return config

    async def set_custom_domain(
        self,
        firm_id: str,
        domain: str,
        ssl_certificate: Optional[str] = None
    ) -> WhiteLabelConfiguration:
        """Configure custom domain"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        # Validate domain format
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, domain):
            raise ValueError("Invalid domain format")

        config = self.configurations[firm_id]
        config.domain_config.custom_domain = domain
        config.domain_config.ssl_certificate = ssl_certificate
        config.updated_at = datetime.now()
        await self._save_configuration(config)

        return config

    async def generate_css(self, firm_id: str) -> str:
        """Generate custom CSS based on configuration"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]

        css = f"""
        /* White-label CSS for {config.firm_name} */
        :root {{
            --primary-color: {config.color_scheme.primary};
            --secondary-color: {config.color_scheme.secondary};
            --accent-color: {config.color_scheme.accent};
            --background-color: {config.color_scheme.background};
            --surface-color: {config.color_scheme.surface};
            --text-primary: {config.color_scheme.text_primary};
            --text-secondary: {config.color_scheme.text_secondary};
            --error-color: {config.color_scheme.error};
            --warning-color: {config.color_scheme.warning};
            --success-color: {config.color_scheme.success};

            --font-primary: {config.typography.font_family_primary};
            --font-secondary: {config.typography.font_family_secondary};
            --font-size-base: {config.typography.font_size_base};
            --font-size-small: {config.typography.font_size_small};
            --font-size-large: {config.typography.font_size_large};
            --font-size-xl: {config.typography.font_size_xl};
            --font-weight-normal: {config.typography.font_weight_normal};
            --font-weight-medium: {config.typography.font_weight_medium};
            --font-weight-bold: {config.typography.font_weight_bold};
            --line-height: {config.typography.line_height};
        }}

        body {{
            font-family: var(--font-primary);
            font-size: var(--font-size-base);
            line-height: var(--line-height);
            color: var(--text-primary);
            background-color: var(--background-color);
        }}

        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
        }}

        .btn-primary:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
        }}

        .navbar-brand img {{
            max-width: {config.logo_config.max_width};
            max-height: {config.logo_config.max_height};
        }}

        .accent {{
            color: var(--accent-color);
        }}

        .bg-accent {{
            background-color: var(--accent-color);
        }}

        .surface {{
            background-color: var(--surface-color);
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: var(--font-secondary);
            font-weight: var(--font-weight-bold);
            color: var(--text-primary);
        }}

        .text-muted {{
            color: var(--text-secondary);
        }}

        .alert-success {{
            background-color: var(--success-color);
            border-color: var(--success-color);
        }}

        .alert-warning {{
            background-color: var(--warning-color);
            border-color: var(--warning-color);
        }}

        .alert-danger {{
            background-color: var(--error-color);
            border-color: var(--error-color);
        }}
        """

        # Add custom CSS if provided
        if config.custom_css:
            css += f"\n\n/* Custom CSS */\n{config.custom_css}"

        return css

    async def generate_email_template(
        self,
        firm_id: str,
        template_type: str,
        content: str
    ) -> str:
        """Generate custom email template"""

        if firm_id not in self.configurations:
            raise ValueError(f"Configuration not found for firm {firm_id}")

        config = self.configurations[firm_id]

        # Base email template
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{config.firm_name}</title>
            <style>
                body {{
                    font-family: {config.typography.font_family_primary};
                    color: {config.color_scheme.text_primary};
                    background-color: {config.color_scheme.background};
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: {config.color_scheme.surface};
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .header {{
                    background-color: {config.color_scheme.primary};
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .footer {{
                    background-color: {config.color_scheme.surface};
                    padding: 20px;
                    text-align: center;
                    font-size: {config.typography.font_size_small};
                    color: {config.color_scheme.text_secondary};
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    {f'<img src="{config.logo_config.logo_url}" alt="{config.firm_name}" style="max-height: 40px;">' if config.logo_config.logo_url else ''}
                    <h1>{config.firm_name}</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>{config.email_templates.footer_signature or f'© {datetime.now().year} {config.firm_name}. All rights reserved.'}</p>
                    {f'<p>Contact: {config.support_email}</p>' if config.support_email else ''}
                </div>
            </div>
        </body>
        </html>
        """

        return template

    async def get_configuration(self, firm_id: str) -> Optional[WhiteLabelConfiguration]:
        """Get white-label configuration"""
        return self.configurations.get(firm_id)

    async def list_configurations(self) -> List[WhiteLabelConfiguration]:
        """List all configurations"""
        return list(self.configurations.values())

    async def _save_configuration(self, config: WhiteLabelConfiguration):
        """Save configuration to storage"""
        config_path = self.storage_path / f"{config.firm_id}_config.json"

        # Convert dataclass to dict for JSON serialization
        config_dict = {
            "firm_id": config.firm_id,
            "firm_name": config.firm_name,
            "branding_theme": config.branding_theme.value,
            "color_scheme": config.color_scheme.__dict__,
            "typography": config.typography.__dict__,
            "logo_config": config.logo_config.__dict__,
            "email_templates": config.email_templates.__dict__,
            "domain_config": config.domain_config.__dict__,
            "module_config": {k: v.value for k, v in config.module_config.__dict__.items()},
            "practice_areas": config.practice_areas.__dict__,
            "localization": {
                **config.localization.__dict__,
                "primary_language": config.localization.primary_language.value,
                "supported_languages": [lang.value for lang in config.localization.supported_languages]
            },
            "custom_css": config.custom_css,
            "custom_js": config.custom_js,
            "custom_footer": config.custom_footer,
            "terms_of_service_url": config.terms_of_service_url,
            "privacy_policy_url": config.privacy_policy_url,
            "support_email": config.support_email,
            "support_phone": config.support_phone,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "is_active": config.is_active
        }

        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)


# Pydantic models for API
class ColorSchemeModel(BaseModel):
    primary: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    secondary: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    accent: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    background: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    surface: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    text_primary: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    text_secondary: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    error: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    warning: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')
    success: str = Field(..., regex=r'^#[0-9a-fA-F]{6}$')


class TypographyModel(BaseModel):
    font_family_primary: str
    font_family_secondary: str
    font_size_base: str
    font_size_small: str
    font_size_large: str
    font_size_xl: str
    font_weight_normal: str
    font_weight_medium: str
    font_weight_bold: str
    line_height: str


class ConfigurationCreateModel(BaseModel):
    firm_name: str = Field(..., min_length=1, max_length=100)
    initial_theme: BrandingTheme = BrandingTheme.PROFESSIONAL


class BrandingUpdateModel(BaseModel):
    color_scheme: Optional[ColorSchemeModel] = None
    typography: Optional[TypographyModel] = None
    theme: Optional[BrandingTheme] = None


class ModulePermissionsModel(BaseModel):
    document_analysis: Optional[ModulePermission] = None
    legal_research: Optional[ModulePermission] = None
    case_management: Optional[ModulePermission] = None
    client_portal: Optional[ModulePermission] = None
    billing_integration: Optional[ModulePermission] = None
    compliance_tools: Optional[ModulePermission] = None
    reporting: Optional[ModulePermission] = None
    api_access: Optional[ModulePermission] = None
    custom_workflows: Optional[ModulePermission] = None
    analytics: Optional[ModulePermission] = None


class LocalizationModel(BaseModel):
    primary_language: LanguageCode
    supported_languages: List[LanguageCode]
    date_format: str
    time_format: str
    currency: str
    timezone: str
    number_format: str


class DomainConfigModel(BaseModel):
    custom_domain: str = Field(..., regex=r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    ssl_certificate: Optional[str] = None


# Global instance
whitelabel_customizer = WhiteLabelCustomizer()


def get_whitelabel_endpoints() -> APIRouter:
    """Get white-label customization FastAPI endpoints"""
    router = APIRouter(prefix="/whitelabel", tags=["whitelabel"])

    @router.post("/configuration/{firm_id}")
    async def create_whitelabel_configuration(
        firm_id: str,
        config_data: ConfigurationCreateModel
    ):
        """Create new white-label configuration"""
        try:
            config = await whitelabel_customizer.create_configuration(
                firm_id, config_data.firm_name, config_data.initial_theme
            )
            return {"status": "created", "firm_id": firm_id, "subdomain": config.domain_config.subdomain}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/configuration/{firm_id}")
    async def get_whitelabel_configuration(firm_id: str):
        """Get white-label configuration"""
        config = await whitelabel_customizer.get_configuration(firm_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return config

    @router.put("/branding/{firm_id}")
    async def update_branding(firm_id: str, branding: BrandingUpdateModel):
        """Update branding configuration"""
        try:
            color_scheme = ColorScheme(**branding.color_scheme.dict()) if branding.color_scheme else None
            typography = Typography(**branding.typography.dict()) if branding.typography else None

            config = await whitelabel_customizer.update_branding(
                firm_id, color_scheme, typography, branding.theme
            )
            return {"status": "updated", "updated_at": config.updated_at}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/logo/{firm_id}")
    async def upload_logo(
        firm_id: str,
        logo_file: UploadFile = File(...),
        logo_type: str = Form("primary")
    ):
        """Upload firm logo"""
        try:
            logo_url = await whitelabel_customizer.upload_logo(firm_id, logo_file, logo_type)
            return {"status": "uploaded", "logo_url": logo_url}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/modules/{firm_id}")
    async def configure_modules(firm_id: str, modules: ModulePermissionsModel):
        """Configure module permissions"""
        try:
            module_dict = {k: v for k, v in modules.dict().items() if v is not None}
            config = await whitelabel_customizer.configure_modules(firm_id, module_dict)
            return {"status": "updated", "updated_at": config.updated_at}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/practice-areas/{firm_id}")
    async def configure_practice_areas(
        firm_id: str,
        primary_areas: List[str],
        custom_features: Optional[Dict[str, Any]] = None
    ):
        """Configure practice area specialization"""
        try:
            config = await whitelabel_customizer.configure_practice_areas(
                firm_id, primary_areas, custom_features
            )
            return {"status": "updated", "updated_at": config.updated_at}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/localization/{firm_id}")
    async def configure_localization(firm_id: str, localization: LocalizationModel):
        """Configure localization settings"""
        try:
            localization_config = LocalizationConfiguration(**localization.dict())
            config = await whitelabel_customizer.configure_localization(firm_id, localization_config)
            return {"status": "updated", "updated_at": config.updated_at}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/domain/{firm_id}")
    async def set_custom_domain(firm_id: str, domain_config: DomainConfigModel):
        """Configure custom domain"""
        try:
            config = await whitelabel_customizer.set_custom_domain(
                firm_id, domain_config.custom_domain, domain_config.ssl_certificate
            )
            return {"status": "updated", "domain": domain_config.custom_domain}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/css/{firm_id}")
    async def get_custom_css(firm_id: str):
        """Get generated CSS for firm"""
        try:
            css = await whitelabel_customizer.generate_css(firm_id)
            return {"css": css}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/email-template/{firm_id}")
    async def generate_email_template(
        firm_id: str,
        template_type: str,
        content: str
    ):
        """Generate custom email template"""
        try:
            template = await whitelabel_customizer.generate_email_template(
                firm_id, template_type, content
            )
            return {"template": template}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/configurations")
    async def list_all_configurations():
        """List all white-label configurations"""
        configs = await whitelabel_customizer.list_configurations()
        return {
            "total": len(configs),
            "configurations": [
                {
                    "firm_id": config.firm_id,
                    "firm_name": config.firm_name,
                    "theme": config.branding_theme.value,
                    "subdomain": config.domain_config.subdomain,
                    "custom_domain": config.domain_config.custom_domain,
                    "created_at": config.created_at,
                    "is_active": config.is_active
                }
                for config in configs
            ]
        }

    return router


async def initialize_whitelabel_system():
    """Initialize the white-label customization system"""
    print("Initializing white-label customization system...")

    # Create sample configuration for demonstration
    sample_config = await whitelabel_customizer.create_configuration(
        "demo_firm", "Demo Law Firm", BrandingTheme.PROFESSIONAL
    )

    print("✓ White-label customizer initialized")
    print("✓ Theme presets configured")
    print("✓ Practice area templates loaded")
    print("✓ File storage system ready")
    print(f"✓ Sample firm created: {sample_config.firm_name} ({sample_config.domain_config.subdomain}.legalai.com)")
    print("🎨 White-label customization system ready!")