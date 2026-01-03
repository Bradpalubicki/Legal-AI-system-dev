"""
Invoice Generation Service

Advanced invoice generation system with customizable templates, automated billing,
and multi-format output support for legal billing.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import asyncio
import logging
import json
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field

from .advanced_models import (
    Invoice, InvoiceLineItem, TimeEntry, ExpenseEntry, BillingMatter,
    BillingRate, TaxRate, DiscountRule, InvoiceTemplate, Payment,
    InvoiceStatus, LineItemType, AuditLog
)
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class InvoiceRequest(BaseModel):
    """Request model for invoice generation."""
    matter_id: int
    billing_period_start: datetime
    billing_period_end: datetime
    template_id: Optional[int] = None
    include_time_entries: bool = True
    include_expenses: bool = True
    apply_discounts: bool = True
    custom_line_items: List[Dict[str, Any]] = Field(default_factory=list)
    invoice_notes: Optional[str] = None
    due_date: Optional[datetime] = None


class InvoicePreview(BaseModel):
    """Invoice preview before generation."""
    matter_name: str
    client_name: str
    billing_period: str
    time_entries_count: int
    time_entries_total: Decimal
    expenses_count: int
    expenses_total: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    line_items_preview: List[Dict[str, Any]]


class InvoiceSummary(BaseModel):
    """Summary statistics for invoices."""
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    overdue_amount: Decimal
    avg_invoice_amount: Decimal
    payment_rate: float


class InvoiceGenerator:
    """
    Advanced invoice generation service with template support and automated billing rules.
    """
    
    def __init__(self):
        self.default_payment_terms = 30  # days
        self.auto_number_enabled = True
        
    async def preview_invoice(
        self,
        invoice_request: InvoiceRequest,
        db: Optional[AsyncSession] = None
    ) -> InvoicePreview:
        """Generate invoice preview without creating actual invoice."""
        if not db:
            async with get_db_session() as db:
                return await self._preview_invoice_impl(invoice_request, db)
        return await self._preview_invoice_impl(invoice_request, db)
    
    async def _preview_invoice_impl(
        self,
        invoice_request: InvoiceRequest,
        db: AsyncSession
    ) -> InvoicePreview:
        """Implementation of invoice preview."""
        # Get matter information
        matter_query = select(BillingMatter).where(
            BillingMatter.id == invoice_request.matter_id
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError(f"Matter {invoice_request.matter_id} not found")
            
        # Get time entries for the period
        time_entries = []
        time_total = Decimal('0')
        
        if invoice_request.include_time_entries:
            time_query = select(TimeEntry).where(
                and_(
                    TimeEntry.matter_id == invoice_request.matter_id,
                    TimeEntry.entry_date >= invoice_request.billing_period_start,
                    TimeEntry.entry_date <= invoice_request.billing_period_end,
                    TimeEntry.billable_minutes > 0,
                    TimeEntry.invoice_id.is_(None)  # Not already invoiced
                )
            )
            time_result = await db.execute(time_query)
            time_entries = time_result.scalars().all()
            time_total = sum(entry.total_amount for entry in time_entries)
            
        # Get expenses for the period
        expenses = []
        expense_total = Decimal('0')
        
        if invoice_request.include_expenses:
            expense_query = select(ExpenseEntry).where(
                and_(
                    ExpenseEntry.matter_id == invoice_request.matter_id,
                    ExpenseEntry.expense_date >= invoice_request.billing_period_start,
                    ExpenseEntry.expense_date <= invoice_request.billing_period_end,
                    ExpenseEntry.billable_amount > 0,
                    ExpenseEntry.invoice_id.is_(None)  # Not already invoiced
                )
            )
            expense_result = await db.execute(expense_query)
            expenses = expense_result.scalars().all()
            expense_total = sum(expense.billable_amount for expense in expenses)
            
        # Calculate subtotal
        subtotal = time_total + expense_total
        
        # Apply discounts
        discount_amount = Decimal('0')
        if invoice_request.apply_discounts:
            discount_amount = await self._calculate_discounts(
                invoice_request.matter_id, subtotal, db
            )
            
        # Calculate taxes
        tax_amount = await self._calculate_taxes(
            invoice_request.matter_id, subtotal - discount_amount, db
        )
        
        # Generate line items preview
        line_items_preview = []
        
        # Time entries summary
        if time_entries:
            line_items_preview.append({
                'type': 'time_summary',
                'description': f'Legal Services ({len(time_entries)} entries)',
                'quantity': len(time_entries),
                'amount': time_total
            })
            
        # Expenses summary
        if expenses:
            line_items_preview.append({
                'type': 'expense_summary',
                'description': f'Expenses ({len(expenses)} items)',
                'quantity': len(expenses),
                'amount': expense_total
            })
            
        # Custom line items
        for custom_item in invoice_request.custom_line_items:
            line_items_preview.append({
                'type': 'custom',
                **custom_item
            })
            
        total_amount = subtotal - discount_amount + tax_amount
        
        return InvoicePreview(
            matter_name=matter.matter_name,
            client_name=matter.client_name,
            billing_period=f"{invoice_request.billing_period_start.strftime('%Y-%m-%d')} to {invoice_request.billing_period_end.strftime('%Y-%m-%d')}",
            time_entries_count=len(time_entries),
            time_entries_total=time_total,
            expenses_count=len(expenses),
            expenses_total=expense_total,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            line_items_preview=line_items_preview
        )
    
    async def generate_invoice(
        self,
        user_id: int,
        invoice_request: InvoiceRequest,
        db: Optional[AsyncSession] = None
    ) -> Invoice:
        """Generate complete invoice with line items."""
        if not db:
            async with get_db_session() as db:
                return await self._generate_invoice_impl(user_id, invoice_request, db)
        return await self._generate_invoice_impl(user_id, invoice_request, db)
    
    async def _generate_invoice_impl(
        self,
        user_id: int,
        invoice_request: InvoiceRequest,
        db: AsyncSession
    ) -> Invoice:
        """Implementation of invoice generation."""
        # Get matter information
        matter_query = select(BillingMatter).where(
            BillingMatter.id == invoice_request.matter_id
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError(f"Matter {invoice_request.matter_id} not found")
            
        # Generate invoice number
        invoice_number = await self._generate_invoice_number(matter.id, db)
        
        # Calculate due date
        due_date = invoice_request.due_date
        if not due_date:
            due_date = datetime.utcnow() + timedelta(days=self.default_payment_terms)
            
        # Create invoice record
        invoice = Invoice(
            matter_id=invoice_request.matter_id,
            invoice_number=invoice_number,
            invoice_date=datetime.utcnow(),
            due_date=due_date,
            billing_period_start=invoice_request.billing_period_start,
            billing_period_end=invoice_request.billing_period_end,
            template_id=invoice_request.template_id,
            status=InvoiceStatus.DRAFT,
            invoice_notes=invoice_request.invoice_notes,
            created_by=user_id
        )
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        # Add time entry line items
        if invoice_request.include_time_entries:
            await self._add_time_entry_line_items(invoice.id, invoice_request, db)
            
        # Add expense line items
        if invoice_request.include_expenses:
            await self._add_expense_line_items(invoice.id, invoice_request, db)
            
        # Add custom line items
        for custom_item in invoice_request.custom_line_items:
            await self._add_custom_line_item(invoice.id, custom_item, user_id, db)
            
        # Calculate totals
        await self._calculate_invoice_totals(invoice.id, invoice_request.apply_discounts, db)
        
        # Update invoice with calculated totals
        await db.refresh(invoice)
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Generated invoice {invoice.invoice_number}",
            {
                'invoice_id': invoice.id,
                'matter_id': invoice_request.matter_id,
                'total_amount': str(invoice.total_amount)
            },
            db
        )
        
        logger.info(f"Invoice generated: {invoice.invoice_number} for matter {matter.matter_name}")
        return invoice
    
    async def _generate_invoice_number(
        self,
        matter_id: int,
        db: AsyncSession
    ) -> str:
        """Generate unique invoice number."""
        if not self.auto_number_enabled:
            return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{matter_id}"
            
        # Get matter information for prefix
        matter_query = select(BillingMatter).where(BillingMatter.id == matter_id)
        result = await db.execute(matter_query)
        matter = result.scalar_one()
        
        # Get next sequence number for this year
        year = datetime.utcnow().year
        sequence_query = select(func.count(Invoice.id)).where(
            and_(
                Invoice.matter_id == matter_id,
                func.extract('year', Invoice.invoice_date) == year
            )
        )
        sequence_result = await db.execute(sequence_query)
        sequence_number = (sequence_result.scalar() or 0) + 1
        
        # Format: MATTER-YYYY-NNNN
        matter_code = matter.matter_number[:6].upper() if matter.matter_number else f"M{matter_id:04d}"
        return f"{matter_code}-{year}-{sequence_number:04d}"
    
    async def _add_time_entry_line_items(
        self,
        invoice_id: int,
        invoice_request: InvoiceRequest,
        db: AsyncSession
    ):
        """Add time entry line items to invoice."""
        # Get time entries for the period
        time_query = select(TimeEntry).where(
            and_(
                TimeEntry.matter_id == invoice_request.matter_id,
                TimeEntry.entry_date >= invoice_request.billing_period_start,
                TimeEntry.entry_date <= invoice_request.billing_period_end,
                TimeEntry.billable_minutes > 0,
                TimeEntry.invoice_id.is_(None)
            )
        ).order_by(TimeEntry.entry_date, TimeEntry.created_at)
        
        result = await db.execute(time_query)
        time_entries = result.scalars().all()
        
        # Group by date and timekeeper for cleaner invoice
        grouped_entries = {}
        for entry in time_entries:
            key = (entry.entry_date.date(), entry.timekeeper)
            if key not in grouped_entries:
                grouped_entries[key] = []
            grouped_entries[key].append(entry)
            
        # Create line items
        for (date, timekeeper), entries in grouped_entries.items():
            total_hours = sum(entry.billable_minutes for entry in entries) / 60
            total_amount = sum(entry.total_amount for entry in entries)
            
            # Create consolidated description
            descriptions = [entry.activity_description[:100] for entry in entries[:3]]
            if len(entries) > 3:
                descriptions.append(f"... and {len(entries) - 3} more activities")
            description = "; ".join(descriptions)
            
            line_item = InvoiceLineItem(
                invoice_id=invoice_id,
                line_item_type=LineItemType.TIME_ENTRY,
                description=f"{date} - Legal Services: {description}",
                quantity=Decimal(str(total_hours)),
                unit_price=entries[0].hourly_rate,
                amount=total_amount,
                timekeeper=str(timekeeper),
                service_date=datetime.combine(date, datetime.min.time())
            )
            
            db.add(line_item)
            
            # Associate time entries with invoice
            for entry in entries:
                entry.invoice_id = invoice_id
                
        await db.commit()
    
    async def _add_expense_line_items(
        self,
        invoice_id: int,
        invoice_request: InvoiceRequest,
        db: AsyncSession
    ):
        """Add expense line items to invoice."""
        # Get expenses for the period
        expense_query = select(ExpenseEntry).where(
            and_(
                ExpenseEntry.matter_id == invoice_request.matter_id,
                ExpenseEntry.expense_date >= invoice_request.billing_period_start,
                ExpenseEntry.expense_date <= invoice_request.billing_period_end,
                ExpenseEntry.billable_amount > 0,
                ExpenseEntry.invoice_id.is_(None)
            )
        ).order_by(ExpenseEntry.expense_date)
        
        result = await db.execute(expense_query)
        expenses = result.scalars().all()
        
        # Create line items for expenses
        for expense in expenses:
            line_item = InvoiceLineItem(
                invoice_id=invoice_id,
                line_item_type=LineItemType.EXPENSE,
                description=f"{expense.expense_date.strftime('%Y-%m-%d')} - {expense.description}",
                quantity=Decimal('1'),
                unit_price=expense.billable_amount,
                amount=expense.billable_amount,
                service_date=expense.expense_date
            )
            
            db.add(line_item)
            
            # Associate expense with invoice
            expense.invoice_id = invoice_id
            
        await db.commit()
    
    async def _add_custom_line_item(
        self,
        invoice_id: int,
        custom_item: Dict[str, Any],
        user_id: int,
        db: AsyncSession
    ):
        """Add custom line item to invoice."""
        line_item = InvoiceLineItem(
            invoice_id=invoice_id,
            line_item_type=LineItemType.CUSTOM,
            description=custom_item.get('description', 'Custom Item'),
            quantity=Decimal(str(custom_item.get('quantity', 1))),
            unit_price=Decimal(str(custom_item.get('unit_price', 0))),
            amount=Decimal(str(custom_item.get('amount', 0))),
            service_date=datetime.utcnow()
        )
        
        db.add(line_item)
        await db.commit()
    
    async def _calculate_invoice_totals(
        self,
        invoice_id: int,
        apply_discounts: bool,
        db: AsyncSession
    ):
        """Calculate and update invoice totals."""
        # Get invoice with line items
        invoice_query = select(Invoice).options(
            joinedload(Invoice.line_items)
        ).where(Invoice.id == invoice_id)
        
        result = await db.execute(invoice_query)
        invoice = result.scalar_one()
        
        # Calculate subtotal
        subtotal = sum(item.amount for item in invoice.line_items)
        
        # Apply discounts
        discount_amount = Decimal('0')
        if apply_discounts:
            discount_amount = await self._calculate_discounts(
                invoice.matter_id, subtotal, db
            )
            
        # Calculate taxes
        tax_amount = await self._calculate_taxes(
            invoice.matter_id, subtotal - discount_amount, db
        )
        
        # Update invoice totals
        invoice.subtotal = subtotal
        invoice.discount_amount = discount_amount
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal - discount_amount + tax_amount
        
        await db.commit()
    
    async def _calculate_discounts(
        self,
        matter_id: int,
        subtotal: Decimal,
        db: AsyncSession
    ) -> Decimal:
        """Calculate applicable discounts."""
        # Get discount rules for matter
        discount_query = select(DiscountRule).where(
            and_(
                DiscountRule.matter_id == matter_id,
                DiscountRule.is_active == True,
                DiscountRule.min_amount <= subtotal
            )
        ).order_by(desc(DiscountRule.discount_percent))
        
        result = await db.execute(discount_query)
        discount_rule = result.scalar_one_or_none()
        
        if not discount_rule:
            return Decimal('0')
            
        if discount_rule.discount_type == 'percentage':
            discount_amount = subtotal * (discount_rule.discount_percent / Decimal('100'))
        else:  # fixed amount
            discount_amount = discount_rule.discount_amount
            
        # Apply maximum discount limit if specified
        if discount_rule.max_discount_amount:
            discount_amount = min(discount_amount, discount_rule.max_discount_amount)
            
        return discount_amount
    
    async def _calculate_taxes(
        self,
        matter_id: int,
        taxable_amount: Decimal,
        db: AsyncSession
    ) -> Decimal:
        """Calculate applicable taxes."""
        # Get tax rates for matter
        tax_query = select(TaxRate).where(
            and_(
                TaxRate.matter_id == matter_id,
                TaxRate.is_active == True
            )
        )
        
        result = await db.execute(tax_query)
        tax_rates = result.scalars().all()
        
        total_tax = Decimal('0')
        
        for tax_rate in tax_rates:
            if tax_rate.tax_type == 'percentage':
                tax_amount = taxable_amount * (tax_rate.rate_percent / Decimal('100'))
            else:  # fixed amount
                tax_amount = tax_rate.fixed_amount
                
            total_tax += tax_amount
            
        return total_tax
    
    async def finalize_invoice(
        self,
        invoice_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> Invoice:
        """Finalize invoice and make it ready for sending."""
        if not db:
            async with get_db_session() as db:
                return await self._finalize_invoice_impl(invoice_id, user_id, db)
        return await self._finalize_invoice_impl(invoice_id, user_id, db)
    
    async def _finalize_invoice_impl(
        self,
        invoice_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Invoice:
        """Implementation of invoice finalization."""
        # Get invoice
        query = select(Invoice).where(Invoice.id == invoice_id)
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ValueError("Invoice not found")
            
        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Can only finalize draft invoices")
            
        # Validate invoice has line items and totals
        if not invoice.line_items or invoice.total_amount <= 0:
            raise ValueError("Invoice must have line items and positive total")
            
        # Update status
        invoice.status = InvoiceStatus.FINALIZED
        invoice.finalized_at = datetime.utcnow()
        invoice.finalized_by = user_id
        
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Finalized invoice {invoice.invoice_number}",
            {
                'invoice_id': invoice.id,
                'total_amount': str(invoice.total_amount)
            },
            db
        )
        
        logger.info(f"Invoice {invoice.invoice_number} finalized")
        return invoice
    
    async def get_invoice_summary(
        self,
        matter_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[AsyncSession] = None
    ) -> InvoiceSummary:
        """Get invoice summary statistics."""
        if not db:
            async with get_db_session() as db:
                return await self._get_invoice_summary_impl(matter_id, start_date, end_date, db)
        return await self._get_invoice_summary_impl(matter_id, start_date, end_date, db)
    
    async def _get_invoice_summary_impl(
        self,
        matter_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: AsyncSession
    ) -> InvoiceSummary:
        """Implementation of invoice summary."""
        # Build query conditions
        conditions = []
        
        if matter_id:
            conditions.append(Invoice.matter_id == matter_id)
        if start_date:
            conditions.append(Invoice.invoice_date >= start_date)
        if end_date:
            conditions.append(Invoice.invoice_date <= end_date)
            
        base_conditions = and_(*conditions) if conditions else None
        
        # Get summary statistics
        summary_query = select(
            func.count(Invoice.id).label('total_invoices'),
            func.sum(Invoice.total_amount).label('total_amount'),
            func.sum(Invoice.paid_amount).label('paid_amount'),
            func.sum(Invoice.total_amount - Invoice.paid_amount).label('outstanding_amount'),
            func.sum(
                func.case(
                    (and_(Invoice.due_date < datetime.utcnow(), Invoice.paid_amount < Invoice.total_amount), 
                     Invoice.total_amount - Invoice.paid_amount),
                    else_=Decimal('0')
                )
            ).label('overdue_amount'),
            func.avg(Invoice.total_amount).label('avg_amount')
        )
        
        if base_conditions is not None:
            summary_query = summary_query.where(base_conditions)
            
        result = await db.execute(summary_query)
        row = result.first()
        
        # Calculate payment rate
        total_amount = row.total_amount or Decimal('0')
        paid_amount = row.paid_amount or Decimal('0')
        payment_rate = float(paid_amount / total_amount) if total_amount > 0 else 0.0
        
        return InvoiceSummary(
            total_invoices=row.total_invoices or 0,
            total_amount=total_amount,
            paid_amount=paid_amount,
            outstanding_amount=row.outstanding_amount or Decimal('0'),
            overdue_amount=row.overdue_amount or Decimal('0'),
            avg_invoice_amount=row.avg_amount or Decimal('0'),
            payment_rate=payment_rate
        )
    
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
            user_agent="InvoiceGenerator"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()