"""
Client Portal Billing Manager

Handles client access to invoices, billing statements, payment tracking,
and financial information with secure access controls.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from decimal import Decimal
import uuid

from .models import (
    ClientInvoice, ClientUser, ClientCase, InvoiceStatus,
    ClientAuditLog, AuditAction
)
from .audit_manager import ClientAuditManager


class ClientBillingManager:
    """Manages client access to billing and invoice information."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_manager = ClientAuditManager(db_session)
    
    async def get_client_invoices(
        self,
        client_id: int,
        status: Optional[InvoiceStatus] = None,
        case_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get invoices for a client with filtering options."""
        try:
            # Validate client exists
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Build query
            query = self.db.query(ClientInvoice).filter(ClientInvoice.client_id == client_id)
            
            # Apply filters
            if status:
                query = query.filter(ClientInvoice.status == status)
            
            if case_id:
                query = query.filter(ClientInvoice.case_id == case_id)
            
            if date_from:
                query = query.filter(ClientInvoice.issued_date >= date_from)
            
            if date_to:
                query = query.filter(ClientInvoice.issued_date <= date_to)
            
            # Get total count
            total_count = query.count()
            
            # Calculate totals for filtered invoices
            totals = query.with_entities(
                func.sum(ClientInvoice.total_amount),
                func.sum(ClientInvoice.subtotal),
                func.sum(ClientInvoice.tax_amount)
            ).first()
            
            total_amount = float(totals[0]) if totals[0] else 0
            total_subtotal = float(totals[1]) if totals[1] else 0
            total_tax = float(totals[2]) if totals[2] else 0
            
            # Apply pagination and ordering
            invoices = query.order_by(desc(ClientInvoice.issued_date)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'invoices': [self._invoice_to_dict(inv) for inv in invoices],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                },
                'totals': {
                    'total_amount': total_amount,
                    'subtotal': total_subtotal,
                    'tax_amount': total_tax
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve invoices: {str(e)}'}
    
    async def get_invoice_details(
        self,
        invoice_id: str,
        client_id: int,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information for a specific invoice."""
        try:
            # Get invoice with access validation
            invoice = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.invoice_id == invoice_id,
                    ClientInvoice.client_id == client_id
                )
            ).first()
            
            if not invoice:
                return {'success': False, 'error': 'Invoice not found or access denied'}
            
            # Log access
            self.audit_manager.log_event(
                user_id=client_id,
                action=AuditAction.INVOICE_VIEWED,
                resource_type='invoice',
                resource_id=invoice_id,
                ip_address=ip_address,
                action_details={
                    'invoice_number': invoice.invoice_number,
                    'total_amount': float(invoice.total_amount) if invoice.total_amount else 0
                }
            )
            
            # Get related case information if applicable
            case_info = None
            if invoice.case_id:
                case = self.db.query(ClientCase).filter(ClientCase.id == invoice.case_id).first()
                if case:
                    case_info = {
                        'case_id': case.case_id,
                        'case_number': case.case_number,
                        'title': case.title
                    }
            
            invoice_dict = self._invoice_to_dict(invoice, include_line_items=True)
            invoice_dict['case'] = case_info
            
            return {
                'success': True,
                'invoice': invoice_dict
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve invoice details: {str(e)}'}
    
    async def get_billing_summary(
        self,
        client_id: int,
        period_months: int = 12
    ) -> Dict[str, Any]:
        """Get billing summary for client dashboard."""
        try:
            # Calculate date range
            start_date = datetime.utcnow() - timedelta(days=period_months * 30)
            
            # Get invoices in period
            invoices = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.client_id == client_id,
                    ClientInvoice.issued_date >= start_date
                )
            ).all()
            
            # Calculate summary statistics
            total_invoiced = sum(float(inv.total_amount) for inv in invoices if inv.total_amount)
            total_paid = sum(float(inv.total_amount) for inv in invoices 
                           if inv.status == InvoiceStatus.PAID and inv.total_amount)
            total_outstanding = sum(float(inv.total_amount) for inv in invoices 
                                  if inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE] and inv.total_amount)
            
            # Count by status
            status_counts = {}
            status_amounts = {}
            for status in InvoiceStatus:
                filtered_invoices = [inv for inv in invoices if inv.status == status]
                status_counts[status.value] = len(filtered_invoices)
                status_amounts[status.value] = sum(float(inv.total_amount) for inv in filtered_invoices if inv.total_amount)
            
            # Get recent invoices
            recent_invoices = self.db.query(ClientInvoice).filter(
                ClientInvoice.client_id == client_id
            ).order_by(desc(ClientInvoice.issued_date)).limit(5).all()
            
            # Get overdue invoices
            overdue_invoices = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.client_id == client_id,
                    ClientInvoice.status == InvoiceStatus.OVERDUE
                )
            ).order_by(ClientInvoice.due_date).all()
            
            # Monthly breakdown
            monthly_totals = {}
            for invoice in invoices:
                if invoice.issued_date:
                    month_key = invoice.issued_date.strftime('%Y-%m')
                    monthly_totals[month_key] = monthly_totals.get(month_key, 0) + float(invoice.total_amount or 0)
            
            return {
                'success': True,
                'summary': {
                    'period_months': period_months,
                    'total_invoiced': total_invoiced,
                    'total_paid': total_paid,
                    'total_outstanding': total_outstanding,
                    'invoice_count': len(invoices),
                    'by_status': {
                        'counts': status_counts,
                        'amounts': status_amounts
                    },
                    'monthly_totals': monthly_totals,
                    'recent_invoices': [
                        {
                            'invoice_id': inv.invoice_id,
                            'invoice_number': inv.invoice_number,
                            'total_amount': float(inv.total_amount) if inv.total_amount else 0,
                            'status': inv.status.value if inv.status else None,
                            'issued_date': inv.issued_date.isoformat() if inv.issued_date else None,
                            'due_date': inv.due_date.isoformat() if inv.due_date else None
                        } for inv in recent_invoices
                    ],
                    'overdue_invoices': [
                        {
                            'invoice_id': inv.invoice_id,
                            'invoice_number': inv.invoice_number,
                            'total_amount': float(inv.total_amount) if inv.total_amount else 0,
                            'due_date': inv.due_date.isoformat() if inv.due_date else None,
                            'days_overdue': (datetime.utcnow() - inv.due_date).days if inv.due_date else 0
                        } for inv in overdue_invoices
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to generate billing summary: {str(e)}'}
    
    async def get_payment_history(
        self,
        client_id: int,
        invoice_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get payment history for client."""
        try:
            # Build query for paid invoices
            query = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.client_id == client_id,
                    ClientInvoice.status == InvoiceStatus.PAID
                )
            )
            
            if invoice_id:
                query = query.filter(ClientInvoice.invoice_id == invoice_id)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            paid_invoices = query.order_by(desc(ClientInvoice.paid_date)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            # Calculate total paid amount
            total_paid = query.with_entities(func.sum(ClientInvoice.total_amount)).scalar() or Decimal('0')
            
            payment_records = []
            for invoice in paid_invoices:
                payment_records.append({
                    'invoice_id': invoice.invoice_id,
                    'invoice_number': invoice.invoice_number,
                    'amount_paid': float(invoice.total_amount) if invoice.total_amount else 0,
                    'payment_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
                    'issued_date': invoice.issued_date.isoformat() if invoice.issued_date else None,
                    'case_id': invoice.case_id,
                    'payment_methods': invoice.payment_methods,
                    'description': invoice.description
                })
            
            return {
                'success': True,
                'payment_history': payment_records,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                },
                'total_paid': float(total_paid)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve payment history: {str(e)}'}
    
    async def get_billing_by_case(
        self,
        client_id: int,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get billing information grouped by case."""
        try:
            # Base query for client's invoices
            base_query = self.db.query(ClientInvoice).filter(ClientInvoice.client_id == client_id)
            
            if case_id:
                # Get specific case billing
                case = self.db.query(ClientCase).filter(
                    and_(
                        ClientCase.case_id == case_id,
                        ClientCase.client_id == client_id
                    )
                ).first()
                
                if not case:
                    return {'success': False, 'error': 'Case not found or access denied'}
                
                invoices = base_query.filter(ClientInvoice.case_id == case.id).all()
                
                case_billing = self._calculate_case_billing(invoices)
                case_billing['case'] = {
                    'case_id': case.case_id,
                    'case_number': case.case_number,
                    'title': case.title
                }
                
                return {
                    'success': True,
                    'case_billing': case_billing
                }
            else:
                # Get billing for all cases
                # Get all client cases
                cases = self.db.query(ClientCase).filter(ClientCase.client_id == client_id).all()
                case_billings = []
                
                for case in cases:
                    case_invoices = base_query.filter(ClientInvoice.case_id == case.id).all()
                    case_billing = self._calculate_case_billing(case_invoices)
                    case_billing['case'] = {
                        'case_id': case.case_id,
                        'case_number': case.case_number,
                        'title': case.title
                    }
                    case_billings.append(case_billing)
                
                # Get invoices not associated with any case
                no_case_invoices = base_query.filter(ClientInvoice.case_id.is_(None)).all()
                if no_case_invoices:
                    no_case_billing = self._calculate_case_billing(no_case_invoices)
                    no_case_billing['case'] = {
                        'case_id': None,
                        'case_number': 'N/A',
                        'title': 'General Billing'
                    }
                    case_billings.append(no_case_billing)
                
                return {
                    'success': True,
                    'case_billings': case_billings
                }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve case billing: {str(e)}'}
    
    async def get_outstanding_balance(self, client_id: int) -> Dict[str, Any]:
        """Get current outstanding balance for client."""
        try:
            # Get all unpaid invoices
            outstanding_invoices = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.client_id == client_id,
                    ClientInvoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])
                )
            ).all()
            
            total_outstanding = sum(float(inv.total_amount) for inv in outstanding_invoices if inv.total_amount)
            
            # Categorize by due date
            current_amount = 0  # Not yet due
            overdue_amount = 0  # Past due
            
            for invoice in outstanding_invoices:
                amount = float(invoice.total_amount) if invoice.total_amount else 0
                if invoice.due_date and invoice.due_date < datetime.utcnow().date():
                    overdue_amount += amount
                else:
                    current_amount += amount
            
            # Get oldest outstanding invoice
            oldest_invoice = None
            if outstanding_invoices:
                oldest = min(outstanding_invoices, key=lambda x: x.issued_date or datetime.max)
                oldest_invoice = {
                    'invoice_id': oldest.invoice_id,
                    'invoice_number': oldest.invoice_number,
                    'amount': float(oldest.total_amount) if oldest.total_amount else 0,
                    'issued_date': oldest.issued_date.isoformat() if oldest.issued_date else None,
                    'due_date': oldest.due_date.isoformat() if oldest.due_date else None
                }
            
            return {
                'success': True,
                'outstanding_balance': {
                    'total_amount': total_outstanding,
                    'current_amount': current_amount,
                    'overdue_amount': overdue_amount,
                    'invoice_count': len(outstanding_invoices),
                    'oldest_invoice': oldest_invoice,
                    'invoices': [
                        {
                            'invoice_id': inv.invoice_id,
                            'invoice_number': inv.invoice_number,
                            'amount': float(inv.total_amount) if inv.total_amount else 0,
                            'due_date': inv.due_date.isoformat() if inv.due_date else None,
                            'status': inv.status.value if inv.status else None,
                            'days_overdue': (datetime.utcnow().date() - inv.due_date).days 
                                          if inv.due_date and inv.due_date < datetime.utcnow().date() else 0
                        } for inv in outstanding_invoices
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to calculate outstanding balance: {str(e)}'}
    
    async def export_billing_statement(
        self,
        client_id: int,
        date_from: datetime,
        date_to: datetime,
        format_type: str = 'summary'  # 'summary' or 'detailed'
    ) -> Dict[str, Any]:
        """Export billing statement for specified period."""
        try:
            # Get invoices in date range
            invoices = self.db.query(ClientInvoice).filter(
                and_(
                    ClientInvoice.client_id == client_id,
                    ClientInvoice.issued_date >= date_from,
                    ClientInvoice.issued_date <= date_to
                )
            ).order_by(ClientInvoice.issued_date).all()
            
            # Get client information
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Generate statement data
            statement = {
                'client': {
                    'name': f"{client.first_name} {client.last_name}",
                    'email': client.email,
                    'company': client.company_name
                },
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'summary': {
                    'total_invoiced': sum(float(inv.total_amount) for inv in invoices if inv.total_amount),
                    'total_paid': sum(float(inv.total_amount) for inv in invoices 
                                    if inv.status == InvoiceStatus.PAID and inv.total_amount),
                    'total_outstanding': sum(float(inv.total_amount) for inv in invoices 
                                           if inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE] and inv.total_amount),
                    'invoice_count': len(invoices)
                }
            }
            
            if format_type == 'detailed':
                statement['invoices'] = [self._invoice_to_dict(inv, include_line_items=True) for inv in invoices]
            else:
                statement['invoices'] = [self._invoice_to_dict(inv) for inv in invoices]
            
            return {
                'success': True,
                'statement': statement
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to export billing statement: {str(e)}'}
    
    def _calculate_case_billing(self, invoices: List[ClientInvoice]) -> Dict[str, Any]:
        """Calculate billing totals for a set of invoices."""
        total_invoiced = sum(float(inv.total_amount) for inv in invoices if inv.total_amount)
        total_paid = sum(float(inv.total_amount) for inv in invoices 
                        if inv.status == InvoiceStatus.PAID and inv.total_amount)
        total_outstanding = sum(float(inv.total_amount) for inv in invoices 
                              if inv.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE] and inv.total_amount)
        
        return {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'invoice_count': len(invoices),
            'invoices': [self._invoice_to_dict(inv) for inv in invoices]
        }
    
    def _invoice_to_dict(self, invoice: ClientInvoice, include_line_items: bool = False) -> Dict[str, Any]:
        """Convert invoice to dictionary representation."""
        invoice_dict = {
            'invoice_id': invoice.invoice_id,
            'invoice_number': invoice.invoice_number,
            'title': invoice.title,
            'description': invoice.description,
            'subtotal': float(invoice.subtotal) if invoice.subtotal else 0,
            'tax_amount': float(invoice.tax_amount) if invoice.tax_amount else 0,
            'discount_amount': float(invoice.discount_amount) if invoice.discount_amount else 0,
            'total_amount': float(invoice.total_amount) if invoice.total_amount else 0,
            'currency': invoice.currency,
            'status': invoice.status.value if invoice.status else None,
            'issued_date': invoice.issued_date.isoformat() if invoice.issued_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'paid_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
            'payment_terms': invoice.payment_terms,
            'payment_methods': invoice.payment_methods,
            'case_id': invoice.case_id,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'created_by': invoice.created_by
        }
        
        if include_line_items:
            invoice_dict['line_items'] = invoice.line_items or []
        
        return invoice_dict