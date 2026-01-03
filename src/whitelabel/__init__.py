"""
White-Label Customization System
Comprehensive branding and customization capabilities for law firms.
"""

from .customization import (
    WhiteLabelCustomizer,
    WhiteLabelConfiguration,
    ColorScheme,
    Typography,
    LogoConfiguration,
    EmailTemplateConfig,
    DomainConfiguration,
    ModuleConfiguration,
    PracticeAreaConfiguration,
    LocalizationConfiguration,
    BrandingTheme,
    LanguageCode,
    ModulePermission,
    ColorSchemeModel,
    TypographyModel,
    ConfigurationCreateModel,
    BrandingUpdateModel,
    ModulePermissionsModel,
    LocalizationModel,
    DomainConfigModel,
    whitelabel_customizer,
    get_whitelabel_endpoints,
    initialize_whitelabel_system
)

__all__ = [
    "WhiteLabelCustomizer",
    "WhiteLabelConfiguration",
    "ColorScheme",
    "Typography",
    "LogoConfiguration",
    "EmailTemplateConfig",
    "DomainConfiguration",
    "ModuleConfiguration",
    "PracticeAreaConfiguration",
    "LocalizationConfiguration",
    "BrandingTheme",
    "LanguageCode",
    "ModulePermission",
    "ColorSchemeModel",
    "TypographyModel",
    "ConfigurationCreateModel",
    "BrandingUpdateModel",
    "ModulePermissionsModel",
    "LocalizationModel",
    "DomainConfigModel",
    "whitelabel_customizer",
    "get_whitelabel_endpoints",
    "initialize_whitelabel_system"
]