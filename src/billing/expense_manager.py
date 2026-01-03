"""
Expense Management Service

Comprehensive expense tracking and reimbursement system for legal billing
with automated categorization and approval workflows.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import asyncio
import logging
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc, asc
from pydantic import BaseModel, Field, validator

from .advanced_models import (
    ExpenseEntry, ExpenseCategory, ExpenseReceipt, BillingMatter,
    BillingRule, AuditLog, ExpenseStatus, ReimbursementStatus,
    ApprovalStatus, ExpenseType
)
from ..core.database import get_db_session
from ..core.security import get_current_user_id


logger = logging.getLogger(__name__)


class ExpenseRequest(BaseModel):
    """Request model for creating expense entries."""
    matter_id: int
    expense_date: datetime
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    expense_type: str
    category: str
    description: str = Field(..., min_length=5, max_length=1000)
    vendor: Optional[str] = None
    receipt_required: bool = True
    billable: bool = True
    reimbursable: bool = False
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class ExpenseSummary(BaseModel):
    """Summary statistics for expenses."""
    total_expenses: Decimal
    billable_expenses: Decimal
    non_billable_expenses: Decimal
    pending_reimbursement: Decimal
    approved_expenses: Decimal
    rejected_expenses: Decimal
    expenses_count: int
    avg_expense_amount: Decimal


class ReceiptUpload(BaseModel):
    """Receipt upload information."""
    filename: str
    file_size: int
    content_type: str
    file_path: str
    ocr_text: Optional[str] = None


class ExpenseManager:
    """
    Advanced expense management service with automated categorization and approval workflows.
    """
    
    def __init__(self):
        self.auto_categorization_enabled = True
        self.ocr_processing_enabled = True
        
    async def create_expense(
        self,
        user_id: int,
        expense_request: ExpenseRequest,
        receipt_files: Optional[List[ReceiptUpload]] = None,
        db: Optional[AsyncSession] = None
    ) -> ExpenseEntry:
        """Create a new expense entry with receipt processing."""
        if not db:
            async with get_db_session() as db:
                return await self._create_expense_impl(
                    user_id, expense_request, receipt_files, db
                )
        return await self._create_expense_impl(
            user_id, expense_request, receipt_files, db
        )
    
    async def _create_expense_impl(
        self,
        user_id: int,
        expense_request: ExpenseRequest,
        receipt_files: Optional[List[ReceiptUpload]],
        db: AsyncSession
    ) -> ExpenseEntry:
        """Implementation of expense creation."""
        # Verify matter exists and user has access
        matter_query = select(BillingMatter).where(
            and_(
                BillingMatter.id == expense_request.matter_id,
                BillingMatter.responsible_attorney == user_id
            )
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError(f"Matter {expense_request.matter_id} not found or access denied")
            
        # Get or create expense category
        category = await self._get_or_create_category(
            expense_request.category, expense_request.expense_type, db
        )
        
        # Apply expense rules and markup
        final_amount, markup_amount = await self._apply_expense_rules(
            expense_request.amount,
            expense_request.matter_id,
            category.id,
            user_id,
            db
        )
        
        # Create expense entry
        expense = ExpenseEntry(
            matter_id=expense_request.matter_id,
            user_id=user_id,
            expense_date=expense_request.expense_date,
            amount=expense_request.amount,
            billable_amount=final_amount if expense_request.billable else Decimal('0'),
            markup_amount=markup_amount,
            expense_type=ExpenseType[expense_request.expense_type.upper()],
            category_id=category.id,
            description=expense_request.description,
            vendor=expense_request.vendor,
            receipt_required=expense_request.receipt_required,
            billable=expense_request.billable,
            reimbursable=expense_request.reimbursable,
            expense_status=ExpenseStatus.DRAFT,
            reimbursement_status=ReimbursementStatus.NOT_REQUESTED if expense_request.reimbursable else None,
            approval_status=ApprovalStatus.PENDING if expense_request.amount >= Decimal('100') else ApprovalStatus.AUTO_APPROVED,
            notes=expense_request.notes,
            tags=expense_request.tags,
            created_by=user_id
        )
        
        db.add(expense)
        await db.commit()
        await db.refresh(expense)
        
        # Process receipt files if provided
        if receipt_files:
            for receipt_file in receipt_files:
                receipt = await self._create_receipt_record(
                    expense.id, receipt_file, user_id, db
                )
                if receipt and self.ocr_processing_enabled:
                    await self._process_receipt_ocr(receipt.id, db)
                    
        # Create audit log
        await self._create_audit_log(
            user_id, 
            f"Created expense entry {expense.expense_id}",
            {
                'expense_id': expense.id,
                'amount': str(expense_request.amount),
                'matter_id': expense_request.matter_id
            },
            db
        )
        
        logger.info(f"Expense entry created: {expense.expense_id} for ${expense_request.amount}")
        return expense
    
    async def _get_or_create_category(
        self,
        category_name: str,
        expense_type: str,
        db: AsyncSession
    ) -> ExpenseCategory:
        """Get existing category or create new one."""
        # Try to find existing category
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.category_name.ilike(f"%{category_name}%"),
                ExpenseCategory.is_active == True
            )
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            return category
            
        # Create new category
        category = ExpenseCategory(
            category_name=category_name.title(),
            category_code=category_name.upper().replace(' ', '_'),
            expense_type=expense_type,
            description=f"Auto-created category for {category_name}",
            is_billable=True,
            requires_receipt=True,
            is_active=True,
            created_by=1  # System user
        )
        
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        logger.info(f"Created new expense category: {category.category_name}")
        return category
    
    async def _apply_expense_rules(
        self,
        amount: Decimal,
        matter_id: int,
        category_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Tuple[Decimal, Decimal]:
        """Apply billing rules to determine final billable amount and markup."""
        # Get applicable billing rules for expenses
        rules_query = select(BillingRule).where(
            and_(
                BillingRule.matter_id == matter_id,
                BillingRule.rule_type.in_(['expense_markup', 'expense_cap', 'expense_multiplier']),
                BillingRule.is_active == True
            )
        ).order_by(BillingRule.priority)
        
        result = await db.execute(rules_query)
        rules = result.scalars().all()
        
        final_amount = amount
        markup_amount = Decimal('0')
        
        for rule in rules:
            if rule.rule_type == 'expense_markup':
                # Apply markup percentage
                markup_percent = Decimal(str(rule.rule_parameters.get('markup_percent', 0))) / Decimal('100')
                markup_amount = amount * markup_percent
                final_amount = amount + markup_amount
                
            elif rule.rule_type == 'expense_multiplier':
                # Apply multiplier (e.g., for certain types of expenses)
                multiplier = Decimal(str(rule.rule_parameters.get('multiplier', 1.0)))
                final_amount = amount * multiplier
                
            elif rule.rule_type == 'expense_cap':
                # Apply cap to prevent excessive expenses
                max_amount = Decimal(str(rule.rule_parameters.get('max_amount', 99999)))
                final_amount = min(final_amount, max_amount)
                
        return final_amount, markup_amount
    
    async def _create_receipt_record(
        self,
        expense_id: int,
        receipt_file: ReceiptUpload,
        user_id: int,
        db: AsyncSession
    ) -> ExpenseReceipt:
        """Create receipt record in database."""
        receipt = ExpenseReceipt(
            expense_id=expense_id,
            filename=receipt_file.filename,
            file_path=receipt_file.file_path,
            file_size=receipt_file.file_size,
            content_type=receipt_file.content_type,
            uploaded_by=user_id,
            upload_timestamp=datetime.utcnow()
        )
        
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        
        logger.info(f"Receipt uploaded for expense {expense_id}: {receipt.filename}")
        return receipt
    
    async def _process_receipt_ocr(
        self,
        receipt_id: int,
        db: AsyncSession
    ):
        """Process receipt with OCR to extract text and validate amounts."""
        # Get receipt record
        query = select(ExpenseReceipt).where(ExpenseReceipt.id == receipt_id)
        result = await db.execute(query)
        receipt = result.scalar_one()
        
        try:
            # In a real implementation, this would use OCR service like AWS Textract
            # or Google Vision API to extract text from the receipt image
            
            # Mock OCR processing
            ocr_text = await self._mock_ocr_processing(receipt.file_path)
            
            # Extract key information from OCR text
            extracted_info = await self._extract_receipt_info(ocr_text)
            
            # Update receipt with OCR results
            receipt.ocr_text = ocr_text
            receipt.ocr_confidence = extracted_info.get('confidence', 0.8)
            receipt.extracted_amount = extracted_info.get('amount')
            receipt.extracted_date = extracted_info.get('date')
            receipt.extracted_vendor = extracted_info.get('vendor')
            receipt.processed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"OCR processing completed for receipt {receipt_id}")
            
        except Exception as e:
            logger.error(f"OCR processing failed for receipt {receipt_id}: {str(e)}")
            receipt.processing_error = str(e)
            await db.commit()
    
    async def _mock_ocr_processing(self, file_path: str) -> str:
        """Mock OCR processing - would be replaced with actual OCR service."""
        return f"RECEIPT\nDate: 2024-01-15\nVendor: Legal Supplies Co.\nAmount: $45.99\nTax: $3.68\nTotal: $49.67"
    
    async def _extract_receipt_info(self, ocr_text: str) -> Dict[str, Any]:
        """Extract structured information from OCR text."""
        # This is a simplified version - real implementation would use
        # more sophisticated NLP and pattern matching
        info = {'confidence': 0.8}
        
        lines = ocr_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.lower().startswith('date:'):
                try:
                    date_str = line.split(':', 1)[1].strip()
                    info['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    pass
                    
            elif line.lower().startswith('vendor:'):
                info['vendor'] = line.split(':', 1)[1].strip()
                
            elif 'total:' in line.lower() or 'amount:' in line.lower():
                # Extract amount using regex would be better
                parts = line.split('$')
                if len(parts) > 1:
                    try:
                        amount_str = parts[1].replace(',', '')
                        info['amount'] = Decimal(amount_str)
                    except:
                        pass
                        
        return info
    
    async def submit_expense(
        self,
        expense_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> ExpenseEntry:
        """Submit expense for approval."""
        if not db:
            async with get_db_session() as db:
                return await self._submit_expense_impl(expense_id, user_id, db)
        return await self._submit_expense_impl(expense_id, user_id, db)
    
    async def _submit_expense_impl(
        self,
        expense_id: int,
        user_id: int,
        db: AsyncSession
    ) -> ExpenseEntry:
        """Implementation of expense submission."""
        # Get expense
        query = select(ExpenseEntry).options(
            joinedload(ExpenseEntry.receipts)
        ).where(
            and_(
                ExpenseEntry.id == expense_id,
                ExpenseEntry.user_id == user_id
            )
        )
        result = await db.execute(query)
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise ValueError("Expense not found or access denied")
            
        if expense.expense_status != ExpenseStatus.DRAFT:
            raise ValueError("Can only submit draft expenses")
            
        # Validate receipt requirements
        if expense.receipt_required and not expense.receipts:
            raise ValueError("Receipt required for this expense")
            
        # Update status
        expense.expense_status = ExpenseStatus.SUBMITTED
        expense.submitted_at = datetime.utcnow()
        
        # Auto-approve small expenses or set pending for larger ones
        if expense.amount < Decimal('50'):
            expense.approval_status = ApprovalStatus.AUTO_APPROVED
            expense.approved_at = datetime.utcnow()
            expense.approved_by = user_id
        else:
            expense.approval_status = ApprovalStatus.PENDING
            
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Submitted expense {expense.expense_id} for approval",
            {'expense_id': expense.id, 'amount': str(expense.amount)},
            db
        )
        
        logger.info(f"Expense {expense.expense_id} submitted for approval")
        return expense
    
    async def approve_expense(
        self,
        expense_id: int,
        approver_id: int,
        approved_amount: Optional[Decimal] = None,
        notes: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> ExpenseEntry:
        """Approve expense entry."""
        if not db:
            async with get_db_session() as db:
                return await self._approve_expense_impl(
                    expense_id, approver_id, approved_amount, notes, db
                )
        return await self._approve_expense_impl(
            expense_id, approver_id, approved_amount, notes, db
        )
    
    async def _approve_expense_impl(
        self,
        expense_id: int,
        approver_id: int,
        approved_amount: Optional[Decimal],
        notes: Optional[str],
        db: AsyncSession
    ) -> ExpenseEntry:
        """Implementation of expense approval."""
        # Get expense
        query = select(ExpenseEntry).where(ExpenseEntry.id == expense_id)
        result = await db.execute(query)
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise ValueError("Expense not found")
            
        if expense.approval_status == ApprovalStatus.APPROVED:
            raise ValueError("Expense already approved")
            
        # Update approval information
        expense.approval_status = ApprovalStatus.APPROVED
        expense.approved_at = datetime.utcnow()
        expense.approved_by = approver_id
        expense.approval_notes = notes
        
        # Update approved amount if different from requested
        if approved_amount and approved_amount != expense.amount:
            expense.approved_amount = approved_amount
            expense.billable_amount = approved_amount if expense.billable else Decimal('0')
        else:
            expense.approved_amount = expense.amount
            
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            approver_id,
            f"Approved expense {expense.expense_id}",
            {
                'expense_id': expense.id,
                'original_amount': str(expense.amount),
                'approved_amount': str(expense.approved_amount)
            },
            db
        )
        
        logger.info(f"Expense {expense.expense_id} approved by user {approver_id}")
        return expense
    
    async def get_expense_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        matter_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> ExpenseSummary:
        """Get expense summary for date range."""
        if not db:
            async with get_db_session() as db:
                return await self._get_expense_summary_impl(
                    user_id, start_date, end_date, matter_id, db
                )
        return await self._get_expense_summary_impl(
            user_id, start_date, end_date, matter_id, db
        )
    
    async def _get_expense_summary_impl(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        matter_id: Optional[int],
        db: AsyncSession
    ) -> ExpenseSummary:
        """Implementation of expense summary."""
        # Build base query
        conditions = [
            ExpenseEntry.user_id == user_id,
            ExpenseEntry.expense_date >= start_date,
            ExpenseEntry.expense_date <= end_date
        ]
        
        if matter_id:
            conditions.append(ExpenseEntry.matter_id == matter_id)
            
        base_query = select(ExpenseEntry).where(and_(*conditions))
        
        # Get summary statistics
        summary_query = select(
            func.sum(ExpenseEntry.amount).label('total_expenses'),
            func.sum(ExpenseEntry.billable_amount).label('billable_expenses'),
            func.sum(
                func.case(
                    (ExpenseEntry.billable == True, ExpenseEntry.amount),
                    else_=Decimal('0')
                ) - ExpenseEntry.billable_amount
            ).label('non_billable_expenses'),
            func.sum(
                func.case(
                    (ExpenseEntry.reimbursement_status == ReimbursementStatus.PENDING, ExpenseEntry.amount),
                    else_=Decimal('0')
                )
            ).label('pending_reimbursement'),
            func.sum(
                func.case(
                    (ExpenseEntry.approval_status == ApprovalStatus.APPROVED, ExpenseEntry.amount),
                    else_=Decimal('0')
                )
            ).label('approved_expenses'),
            func.sum(
                func.case(
                    (ExpenseEntry.approval_status == ApprovalStatus.REJECTED, ExpenseEntry.amount),
                    else_=Decimal('0')
                )
            ).label('rejected_expenses'),
            func.count(ExpenseEntry.id).label('expenses_count'),
            func.avg(ExpenseEntry.amount).label('avg_amount')
        ).where(and_(*conditions))
        
        result = await db.execute(summary_query)
        row = result.first()
        
        return ExpenseSummary(
            total_expenses=row.total_expenses or Decimal('0'),
            billable_expenses=row.billable_expenses or Decimal('0'),
            non_billable_expenses=row.non_billable_expenses or Decimal('0'),
            pending_reimbursement=row.pending_reimbursement or Decimal('0'),
            approved_expenses=row.approved_expenses or Decimal('0'),
            rejected_expenses=row.rejected_expenses or Decimal('0'),
            expenses_count=row.expenses_count or 0,
            avg_expense_amount=row.avg_amount or Decimal('0')
        )
    
    async def request_reimbursement(
        self,
        expense_ids: List[int],
        user_id: int,
        reimbursement_notes: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> List[ExpenseEntry]:
        """Request reimbursement for approved expenses."""
        if not db:
            async with get_db_session() as db:
                return await self._request_reimbursement_impl(
                    expense_ids, user_id, reimbursement_notes, db
                )
        return await self._request_reimbursement_impl(
            expense_ids, user_id, reimbursement_notes, db
        )
    
    async def _request_reimbursement_impl(
        self,
        expense_ids: List[int],
        user_id: int,
        reimbursement_notes: Optional[str],
        db: AsyncSession
    ) -> List[ExpenseEntry]:
        """Implementation of reimbursement request."""
        # Get expenses
        query = select(ExpenseEntry).where(
            and_(
                ExpenseEntry.id.in_(expense_ids),
                ExpenseEntry.user_id == user_id,
                ExpenseEntry.reimbursable == True,
                ExpenseEntry.approval_status == ApprovalStatus.APPROVED,
                ExpenseEntry.reimbursement_status.in_([
                    ReimbursementStatus.NOT_REQUESTED,
                    ReimbursementStatus.REJECTED
                ])
            )
        )
        
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        if not expenses:
            raise ValueError("No eligible expenses found for reimbursement")
            
        # Update reimbursement status
        for expense in expenses:
            expense.reimbursement_status = ReimbursementStatus.PENDING
            expense.reimbursement_requested_at = datetime.utcnow()
            expense.reimbursement_notes = reimbursement_notes
            
        await db.commit()
        
        # Create audit log
        total_amount = sum(expense.approved_amount or expense.amount for expense in expenses)
        await self._create_audit_log(
            user_id,
            f"Requested reimbursement for {len(expenses)} expenses",
            {
                'expense_ids': expense_ids,
                'total_amount': str(total_amount),
                'expense_count': len(expenses)
            },
            db
        )
        
        logger.info(f"Reimbursement requested for {len(expenses)} expenses totaling ${total_amount}")
        return expenses
    
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
            user_agent="ExpenseManager"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()