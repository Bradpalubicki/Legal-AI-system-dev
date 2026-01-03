"""
Payment Methods Management

Secure storage and management of client payment methods with tokenization
and PCI compliance features.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import asyncio
import logging
import json
import uuid
import hashlib
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field, validator
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .advanced_models import (
    PaymentMethod, BillingMatter, AuditLog
)
from .payment_processor import PaymentMethodType
from ..core.database import get_db_session
from ..core.security import get_current_user_id


logger = logging.getLogger(__name__)


class PaymentMethodCreate(BaseModel):
    """Request model for creating payment methods."""
    method_type: PaymentMethodType
    method_name: str = Field(..., min_length=3, max_length=100)
    is_default: bool = False
    
    # Address information
    billing_address: Dict[str, str] = Field(default_factory=dict)
    
    # Credit/Debit Card fields (will be encrypted)
    card_number: Optional[str] = None
    expiry_month: Optional[int] = Field(None, ge=1, le=12)
    expiry_year: Optional[int] = Field(None, ge=2024)
    cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    cardholder_name: Optional[str] = None
    
    # ACH fields (will be encrypted)
    routing_number: Optional[str] = Field(None, regex=r'^\d{9}$')
    account_number: Optional[str] = None
    account_type: Optional[str] = Field(None, regex=r'^(checking|savings)$')
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    
    # Additional secure data
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('card_number')
    def validate_card_number(cls, v):
        if v:
            # Remove spaces and dashes
            clean_number = v.replace(' ', '').replace('-', '')
            if not clean_number.isdigit() or len(clean_number) < 13 or len(clean_number) > 19:
                raise ValueError('Invalid card number format')
        return v
    
    @validator('cvv')
    def validate_cvv(cls, v):
        if v and not v.isdigit():
            raise ValueError('CVV must contain only digits')
        return v


class PaymentMethodResponse(BaseModel):
    """Response model for payment methods (excludes sensitive data)."""
    id: int
    method_type: str
    method_name: str
    is_default: bool
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    
    # Masked sensitive information
    masked_card_number: Optional[str] = None
    card_brand: Optional[str] = None
    expiry_display: Optional[str] = None
    masked_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Billing address (non-sensitive)
    billing_address: Dict[str, str] = Field(default_factory=dict)


class SecurityConfig:
    """Security configuration for payment method encryption."""
    
    def __init__(self):
        # In production, these should come from secure environment variables
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for payment data."""
        # In production, this should be retrieved from a secure key management service
        password = b"secure_payment_encryption_key_2024"  # Should be from env
        salt = b"payment_salt_12345"  # Should be random and stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive payment data."""
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive payment data."""
        if not encrypted_data:
            return ""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()


class PaymentMethodManager:
    """
    Secure payment method management with encryption and PCI compliance features.
    """
    
    def __init__(self):
        self.security = SecurityConfig()
        self.card_brands = {
            '4': 'visa',
            '5': 'mastercard',
            '3': 'amex',
            '6': 'discover'
        }
        
    async def create_payment_method(
        self,
        user_id: int,
        matter_id: int,
        method_data: PaymentMethodCreate,
        db: Optional[AsyncSession] = None
    ) -> PaymentMethodResponse:
        """Create new payment method with secure data storage."""
        if not db:
            async with get_db_session() as db:
                return await self._create_payment_method_impl(user_id, matter_id, method_data, db)
        return await self._create_payment_method_impl(user_id, matter_id, method_data, db)
    
    async def _create_payment_method_impl(
        self,
        user_id: int,
        matter_id: int,
        method_data: PaymentMethodCreate,
        db: AsyncSession
    ) -> PaymentMethodResponse:
        """Implementation of payment method creation."""
        # Verify matter access
        matter_query = select(BillingMatter).where(
            and_(
                BillingMatter.id == matter_id,
                BillingMatter.responsible_attorney == user_id
            )
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError("Matter not found or access denied")
            
        # If this is set as default, unset other defaults
        if method_data.is_default:
            await self._unset_default_methods(matter_id, db)
            
        # Prepare secure data
        secure_data = {}
        
        if method_data.method_type in [PaymentMethodType.CREDIT_CARD, PaymentMethodType.DEBIT_CARD]:
            secure_data = await self._prepare_card_data(method_data)
        elif method_data.method_type == PaymentMethodType.ACH:
            secure_data = await self._prepare_ach_data(method_data)
        else:
            secure_data = method_data.additional_data
            
        # Generate secure token for this payment method
        payment_token = self._generate_payment_token()
        
        # Create payment method record
        payment_method = PaymentMethod(
            matter_id=matter_id,
            user_id=user_id,
            method_type=method_data.method_type,
            method_name=method_data.method_name,
            payment_token=payment_token,
            secure_data=secure_data,  # This will be encrypted at database level
            billing_address=method_data.billing_address,
            is_default=method_data.is_default,
            is_active=True,
            created_by=user_id
        )
        
        db.add(payment_method)
        await db.commit()
        await db.refresh(payment_method)
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Created payment method: {method_data.method_name}",
            {
                'payment_method_id': payment_method.id,
                'method_type': str(method_data.method_type),
                'matter_id': matter_id
            },
            db
        )
        
        logger.info(f"Payment method created: {payment_method.method_name} for matter {matter_id}")
        
        # Return safe response (no sensitive data)
        return await self._build_safe_response(payment_method)
    
    async def _prepare_card_data(self, method_data: PaymentMethodCreate) -> Dict[str, Any]:
        """Prepare and encrypt credit card data."""
        card_data = {}
        
        if method_data.card_number:
            # Encrypt full card number
            card_data['encrypted_card_number'] = self.security.encrypt_data(method_data.card_number)
            
            # Store masked version for display
            clean_number = method_data.card_number.replace(' ', '').replace('-', '')
            card_data['masked_number'] = f"****-****-****-{clean_number[-4:]}"
            
            # Detect card brand
            card_data['brand'] = self._detect_card_brand(clean_number)
            
        if method_data.cvv:
            card_data['encrypted_cvv'] = self.security.encrypt_data(method_data.cvv)
            
        if method_data.cardholder_name:
            card_data['cardholder_name'] = method_data.cardholder_name
            
        if method_data.expiry_month and method_data.expiry_year:
            card_data['expiry_month'] = method_data.expiry_month
            card_data['expiry_year'] = method_data.expiry_year
            card_data['expiry_display'] = f"{method_data.expiry_month:02d}/{method_data.expiry_year}"
            
        return card_data
    
    async def _prepare_ach_data(self, method_data: PaymentMethodCreate) -> Dict[str, Any]:
        """Prepare and encrypt ACH bank account data."""
        ach_data = {}
        
        if method_data.routing_number:
            ach_data['encrypted_routing'] = self.security.encrypt_data(method_data.routing_number)
            
        if method_data.account_number:
            ach_data['encrypted_account'] = self.security.encrypt_data(method_data.account_number)
            # Store masked version
            ach_data['masked_account'] = f"****{method_data.account_number[-4:]}"
            
        if method_data.account_type:
            ach_data['account_type'] = method_data.account_type
            
        if method_data.bank_name:
            ach_data['bank_name'] = method_data.bank_name
            
        if method_data.account_holder_name:
            ach_data['account_holder_name'] = method_data.account_holder_name
            
        return ach_data
    
    def _detect_card_brand(self, card_number: str) -> str:
        """Detect credit card brand from card number."""
        first_digit = card_number[0]
        
        if first_digit == '4':
            return 'visa'
        elif first_digit == '5' or card_number[:2] in ['22', '23', '24', '25', '26', '27']:
            return 'mastercard'
        elif card_number[:2] in ['34', '37']:
            return 'amex'
        elif first_digit == '6':
            return 'discover'
        else:
            return 'unknown'
    
    def _generate_payment_token(self) -> str:
        """Generate secure token for payment method."""
        return f"pm_{uuid.uuid4().hex[:24]}"
    
    async def _unset_default_methods(self, matter_id: int, db: AsyncSession):
        """Unset all default payment methods for a matter."""
        update_query = select(PaymentMethod).where(
            and_(
                PaymentMethod.matter_id == matter_id,
                PaymentMethod.is_default == True,
                PaymentMethod.is_active == True
            )
        )
        
        result = await db.execute(update_query)
        methods = result.scalars().all()
        
        for method in methods:
            method.is_default = False
            
        await db.commit()
    
    async def get_payment_methods(
        self,
        user_id: int,
        matter_id: Optional[int] = None,
        include_inactive: bool = False,
        db: Optional[AsyncSession] = None
    ) -> List[PaymentMethodResponse]:
        """Get user's payment methods."""
        if not db:
            async with get_db_session() as db:
                return await self._get_payment_methods_impl(user_id, matter_id, include_inactive, db)
        return await self._get_payment_methods_impl(user_id, matter_id, include_inactive, db)
    
    async def _get_payment_methods_impl(
        self,
        user_id: int,
        matter_id: Optional[int],
        include_inactive: bool,
        db: AsyncSession
    ) -> List[PaymentMethodResponse]:
        """Implementation of payment methods retrieval."""
        conditions = [PaymentMethod.user_id == user_id]
        
        if matter_id:
            conditions.append(PaymentMethod.matter_id == matter_id)
        if not include_inactive:
            conditions.append(PaymentMethod.is_active == True)
            
        query = select(PaymentMethod).where(
            and_(*conditions)
        ).order_by(desc(PaymentMethod.is_default), desc(PaymentMethod.created_at))
        
        result = await db.execute(query)
        payment_methods = result.scalars().all()
        
        # Convert to safe response format
        responses = []
        for method in payment_methods:
            response = await self._build_safe_response(method)
            responses.append(response)
            
        return responses
    
    async def _build_safe_response(self, payment_method: PaymentMethod) -> PaymentMethodResponse:
        """Build safe response without sensitive data."""
        secure_data = payment_method.secure_data or {}
        
        # Extract masked/safe data based on method type
        masked_card_number = None
        card_brand = None
        expiry_display = None
        masked_account_number = None
        bank_name = None
        
        if payment_method.method_type in ['credit_card', 'debit_card']:
            masked_card_number = secure_data.get('masked_number')
            card_brand = secure_data.get('brand')
            expiry_display = secure_data.get('expiry_display')
        elif payment_method.method_type == 'ach':
            masked_account_number = secure_data.get('masked_account')
            bank_name = secure_data.get('bank_name')
            
        return PaymentMethodResponse(
            id=payment_method.id,
            method_type=payment_method.method_type,
            method_name=payment_method.method_name,
            is_default=payment_method.is_default,
            is_active=payment_method.is_active,
            created_at=payment_method.created_at,
            last_used_at=payment_method.last_used_at,
            masked_card_number=masked_card_number,
            card_brand=card_brand,
            expiry_display=expiry_display,
            masked_account_number=masked_account_number,
            bank_name=bank_name,
            billing_address=payment_method.billing_address or {}
        )
    
    async def update_payment_method(
        self,
        payment_method_id: int,
        user_id: int,
        updates: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> PaymentMethodResponse:
        """Update payment method (non-sensitive fields only)."""
        if not db:
            async with get_db_session() as db:
                return await self._update_payment_method_impl(payment_method_id, user_id, updates, db)
        return await self._update_payment_method_impl(payment_method_id, user_id, updates, db)
    
    async def _update_payment_method_impl(
        self,
        payment_method_id: int,
        user_id: int,
        updates: Dict[str, Any],
        db: AsyncSession
    ) -> PaymentMethodResponse:
        """Implementation of payment method update."""
        # Get payment method
        query = select(PaymentMethod).where(
            and_(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id
            )
        )
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            raise ValueError("Payment method not found or access denied")
            
        # Update allowed fields
        allowed_updates = ['method_name', 'billing_address', 'is_default']
        
        for field, value in updates.items():
            if field in allowed_updates:
                if field == 'is_default' and value:
                    # Unset other default methods
                    await self._unset_default_methods(payment_method.matter_id, db)
                setattr(payment_method, field, value)
                
        payment_method.updated_at = datetime.utcnow()
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Updated payment method: {payment_method.method_name}",
            {
                'payment_method_id': payment_method.id,
                'updated_fields': list(updates.keys())
            },
            db
        )
        
        return await self._build_safe_response(payment_method)
    
    async def delete_payment_method(
        self,
        payment_method_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Soft delete payment method."""
        if not db:
            async with get_db_session() as db:
                return await self._delete_payment_method_impl(payment_method_id, user_id, db)
        return await self._delete_payment_method_impl(payment_method_id, user_id, db)
    
    async def _delete_payment_method_impl(
        self,
        payment_method_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """Implementation of payment method deletion."""
        # Get payment method
        query = select(PaymentMethod).where(
            and_(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id
            )
        )
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            raise ValueError("Payment method not found or access denied")
            
        # Soft delete
        payment_method.is_active = False
        payment_method.deleted_at = datetime.utcnow()
        
        # If this was the default, need to set another as default
        if payment_method.is_default:
            await self._set_new_default_method(payment_method.matter_id, payment_method.id, db)
            
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Deleted payment method: {payment_method.method_name}",
            {
                'payment_method_id': payment_method.id,
                'method_type': payment_method.method_type
            },
            db
        )
        
        return True
    
    async def _set_new_default_method(
        self,
        matter_id: int,
        excluded_method_id: int,
        db: AsyncSession
    ):
        """Set a new default payment method when current default is deleted."""
        query = select(PaymentMethod).where(
            and_(
                PaymentMethod.matter_id == matter_id,
                PaymentMethod.is_active == True,
                PaymentMethod.id != excluded_method_id
            )
        ).order_by(desc(PaymentMethod.created_at)).limit(1)
        
        result = await db.execute(query)
        new_default = result.scalar_one_or_none()
        
        if new_default:
            new_default.is_default = True
            await db.commit()
    
    async def get_decrypted_payment_data(
        self,
        payment_method_id: int,
        user_id: int,
        purpose: str,  # For audit logging
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get decrypted payment data for processing (RESTRICTED ACCESS)."""
        if not db:
            async with get_db_session() as db:
                return await self._get_decrypted_payment_data_impl(payment_method_id, user_id, purpose, db)
        return await self._get_decrypted_payment_data_impl(payment_method_id, user_id, purpose, db)
    
    async def _get_decrypted_payment_data_impl(
        self,
        payment_method_id: int,
        user_id: int,
        purpose: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of decrypted data retrieval."""
        # Get payment method
        query = select(PaymentMethod).where(
            and_(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_active == True
            )
        )
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            raise ValueError("Payment method not found or access denied")
            
        # Decrypt sensitive data
        secure_data = payment_method.secure_data or {}
        decrypted_data = {}
        
        try:
            if payment_method.method_type in ['credit_card', 'debit_card']:
                if 'encrypted_card_number' in secure_data:
                    decrypted_data['card_number'] = self.security.decrypt_data(secure_data['encrypted_card_number'])
                if 'encrypted_cvv' in secure_data:
                    decrypted_data['cvv'] = self.security.decrypt_data(secure_data['encrypted_cvv'])
                    
                # Copy non-encrypted data
                for key in ['cardholder_name', 'expiry_month', 'expiry_year', 'brand']:
                    if key in secure_data:
                        decrypted_data[key] = secure_data[key]
                        
            elif payment_method.method_type == 'ach':
                if 'encrypted_routing' in secure_data:
                    decrypted_data['routing_number'] = self.security.decrypt_data(secure_data['encrypted_routing'])
                if 'encrypted_account' in secure_data:
                    decrypted_data['account_number'] = self.security.decrypt_data(secure_data['encrypted_account'])
                    
                # Copy non-encrypted data
                for key in ['account_type', 'bank_name', 'account_holder_name']:
                    if key in secure_data:
                        decrypted_data[key] = secure_data[key]
                        
            # Update last used timestamp
            payment_method.last_used_at = datetime.utcnow()
            await db.commit()
            
            # Create audit log for sensitive data access
            await self._create_audit_log(
                user_id,
                f"Accessed payment method data: {purpose}",
                {
                    'payment_method_id': payment_method.id,
                    'purpose': purpose,
                    'method_type': payment_method.method_type
                },
                db
            )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt payment data: {str(e)}")
            raise ValueError("Failed to decrypt payment data")
    
    async def validate_payment_method(
        self,
        payment_method_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Validate payment method (e.g., check card expiry)."""
        if not db:
            async with get_db_session() as db:
                return await self._validate_payment_method_impl(payment_method_id, user_id, db)
        return await self._validate_payment_method_impl(payment_method_id, user_id, db)
    
    async def _validate_payment_method_impl(
        self,
        payment_method_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of payment method validation."""
        # Get payment method
        query = select(PaymentMethod).where(
            and_(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id
            )
        )
        result = await db.execute(query)
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            return {
                'valid': False,
                'errors': ['Payment method not found']
            }
            
        if not payment_method.is_active:
            return {
                'valid': False,
                'errors': ['Payment method is inactive']
            }
            
        errors = []
        warnings = []
        
        # Validate based on method type
        if payment_method.method_type in ['credit_card', 'debit_card']:
            secure_data = payment_method.secure_data or {}
            
            # Check expiry
            if 'expiry_year' in secure_data and 'expiry_month' in secure_data:
                expiry_year = secure_data['expiry_year']
                expiry_month = secure_data['expiry_month']
                
                current_date = datetime.utcnow()
                expiry_date = datetime(expiry_year, expiry_month, 1)
                
                if expiry_date < current_date:
                    errors.append('Card has expired')
                elif expiry_date < current_date + timedelta(days=30):
                    warnings.append('Card expires soon')
                    
        elif payment_method.method_type == 'ach':
            # ACH validation would include routing number validation
            secure_data = payment_method.secure_data or {}
            
            if 'account_type' not in secure_data:
                errors.append('Account type not specified')
                
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def _create_audit_log(
        self,
        user_id: int,
        action: str,
        details: Dict[str, Any],
        db: AsyncSession
    ):
        """Create audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address="127.0.0.1",  # Should be passed from request
            user_agent="PaymentMethodManager"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()