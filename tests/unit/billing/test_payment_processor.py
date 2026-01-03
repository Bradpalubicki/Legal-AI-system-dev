"""
Unit tests for billing and payment processing system.

Tests payment processing, invoice generation, subscription management,
billing calculations, and payment gateway integrations.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional
import uuid

from src.billing.payment_processor import PaymentProcessor
from src.billing.models import Invoice, Payment, Subscription, BillingAccount, PaymentMethod
from src.billing.enums import PaymentStatus, InvoiceStatus, SubscriptionStatus, PaymentMethodType
from src.billing.exceptions import PaymentError, InsufficientFundsError, InvalidPaymentMethodError
from src.billing.gateways.stripe_gateway import StripePaymentGateway
from src.billing.gateways.paypal_gateway import PayPalPaymentGateway
from src.shared.models.user import User


class TestPaymentProcessor:
    """Test suite for PaymentProcessor class."""

    @pytest.fixture
    def payment_processor(self, mock_db_session):
        """Create PaymentProcessor instance with mocked database."""
        return PaymentProcessor(db_session=mock_db_session)

    @pytest.fixture
    def mock_stripe_gateway(self):
        """Mock Stripe payment gateway."""
        gateway = Mock(spec=StripePaymentGateway)
        gateway.process_payment = AsyncMock()
        gateway.create_customer = AsyncMock()
        gateway.add_payment_method = AsyncMock()
        gateway.create_subscription = AsyncMock()
        gateway.cancel_subscription = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_paypal_gateway(self):
        """Mock PayPal payment gateway."""
        gateway = Mock(spec=PayPalPaymentGateway)
        gateway.process_payment = AsyncMock()
        gateway.create_customer = AsyncMock()
        gateway.add_payment_method = AsyncMock()
        return gateway

    @pytest.fixture
    def sample_payment_data(self):
        """Sample payment data for testing."""
        return {
            "amount": Decimal("99.99"),
            "currency": "USD",
            "payment_method_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "description": "Legal document analysis - Premium plan",
            "invoice_id": str(uuid.uuid4())
        }

    @pytest.fixture
    def sample_invoice_data(self):
        """Sample invoice data for testing."""
        return {
            "customer_id": str(uuid.uuid4()),
            "amount": Decimal("299.99"),
            "currency": "USD",
            "description": "Monthly subscription - Enterprise plan",
            "due_date": datetime.now() + timedelta(days=30),
            "line_items": [
                {
                    "description": "Enterprise Plan Subscription",
                    "quantity": 1,
                    "unit_price": Decimal("299.99"),
                    "total": Decimal("299.99")
                }
            ]
        }

    @pytest.fixture
    def mock_invoice(self, sample_invoice_data):
        """Mock Invoice object."""
        invoice = Mock(spec=Invoice)
        invoice.id = str(uuid.uuid4())
        invoice.invoice_number = "INV-2024-001"
        invoice.customer_id = sample_invoice_data["customer_id"]
        invoice.amount = sample_invoice_data["amount"]
        invoice.currency = sample_invoice_data["currency"]
        invoice.status = InvoiceStatus.PENDING
        invoice.created_at = datetime.now()
        invoice.due_date = sample_invoice_data["due_date"]
        return invoice

    @pytest.fixture
    def mock_payment_method(self):
        """Mock PaymentMethod object."""
        method = Mock(spec=PaymentMethod)
        method.id = str(uuid.uuid4())
        method.type = PaymentMethodType.CREDIT_CARD
        method.last_four = "4242"
        method.brand = "visa"
        method.is_default = True
        method.is_active = True
        return method

    @pytest.mark.asyncio
    async def test_process_payment_success(self, payment_processor, sample_payment_data, mock_stripe_gateway, mock_db_session):
        """Test successful payment processing."""
        # Arrange
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        
        mock_payment_response = {
            "id": "pi_test_123",
            "status": "succeeded",
            "amount": int(sample_payment_data["amount"] * 100),
            "currency": sample_payment_data["currency"]
        }
        mock_stripe_gateway.process_payment.return_value = mock_payment_response
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.billing.models.Payment') as MockPayment:
            mock_payment_instance = Mock()
            mock_payment_instance.id = str(uuid.uuid4())
            MockPayment.return_value = mock_payment_instance
            
            # Act
            result = await payment_processor.process_payment(sample_payment_data, gateway="stripe")
            
            # Assert
            assert result is not None
            assert result.id is not None
            mock_stripe_gateway.process_payment.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_payment_insufficient_funds(self, payment_processor, sample_payment_data, mock_stripe_gateway):
        """Test payment processing with insufficient funds."""
        # Arrange
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        mock_stripe_gateway.process_payment.side_effect = InsufficientFundsError("Insufficient funds")
        
        # Act & Assert
        with pytest.raises(InsufficientFundsError):
            await payment_processor.process_payment(sample_payment_data, gateway="stripe")

    @pytest.mark.asyncio
    async def test_create_invoice_success(self, payment_processor, sample_invoice_data, mock_db_session):
        """Test successful invoice creation."""
        # Arrange
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        with patch('src.billing.models.Invoice') as MockInvoice:
            mock_invoice_instance = Mock()
            mock_invoice_instance.id = str(uuid.uuid4())
            mock_invoice_instance.invoice_number = "INV-2024-001"
            MockInvoice.return_value = mock_invoice_instance
            
            with patch.object(payment_processor, '_generate_invoice_number', return_value="INV-2024-001"):
                # Act
                result = await payment_processor.create_invoice(sample_invoice_data)
                
                # Assert
                assert result is not None
                assert result.invoice_number == "INV-2024-001"
                MockInvoice.assert_called_once()
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pay_invoice_success(self, payment_processor, mock_invoice, sample_payment_data, mock_db_session):
        """Test successful invoice payment."""
        # Arrange
        invoice_id = mock_invoice.id
        mock_db_session.get = AsyncMock(return_value=mock_invoice)
        mock_db_session.commit = AsyncMock()
        
        with patch.object(payment_processor, 'process_payment') as mock_process_payment:
            mock_payment = Mock()
            mock_payment.status = PaymentStatus.COMPLETED
            mock_process_payment.return_value = mock_payment
            
            # Act
            result = await payment_processor.pay_invoice(invoice_id, sample_payment_data)
            
            # Assert
            assert result.status == InvoiceStatus.PAID
            assert mock_invoice.status == InvoiceStatus.PAID
            assert mock_invoice.paid_at is not None
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, payment_processor, mock_db_session, mock_stripe_gateway):
        """Test successful subscription creation."""
        # Arrange
        subscription_data = {
            "customer_id": str(uuid.uuid4()),
            "plan_id": "enterprise_monthly",
            "payment_method_id": str(uuid.uuid4()),
            "start_date": datetime.now()
        }
        
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        
        mock_stripe_response = {
            "id": "sub_test_123",
            "status": "active",
            "current_period_start": int(datetime.now().timestamp()),
            "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp())
        }
        mock_stripe_gateway.create_subscription.return_value = mock_stripe_response
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.billing.models.Subscription') as MockSubscription:
            mock_subscription_instance = Mock()
            mock_subscription_instance.id = str(uuid.uuid4())
            MockSubscription.return_value = mock_subscription_instance
            
            # Act
            result = await payment_processor.create_subscription(subscription_data)
            
            # Assert
            assert result is not None
            mock_stripe_gateway.create_subscription.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription_success(self, payment_processor, mock_db_session, mock_stripe_gateway):
        """Test successful subscription cancellation."""
        # Arrange
        subscription_id = str(uuid.uuid4())
        mock_subscription = Mock(spec=Subscription)
        mock_subscription.id = subscription_id
        mock_subscription.gateway_subscription_id = "sub_test_123"
        mock_subscription.status = SubscriptionStatus.ACTIVE
        
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        mock_db_session.get = AsyncMock(return_value=mock_subscription)
        mock_db_session.commit = AsyncMock()
        mock_stripe_gateway.cancel_subscription.return_value = {"status": "canceled"}
        
        # Act
        result = await payment_processor.cancel_subscription(subscription_id, "Customer request")
        
        # Assert
        assert result.status == SubscriptionStatus.CANCELED
        assert mock_subscription.canceled_at is not None
        mock_stripe_gateway.cancel_subscription.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_payment_method_success(self, payment_processor, mock_db_session, mock_stripe_gateway):
        """Test successful payment method addition."""
        # Arrange
        customer_id = str(uuid.uuid4())
        payment_method_data = {
            "type": PaymentMethodType.CREDIT_CARD,
            "token": "pm_test_card",
            "is_default": True
        }
        
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        
        mock_stripe_response = {
            "id": "pm_test_123",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025
            }
        }
        mock_stripe_gateway.add_payment_method.return_value = mock_stripe_response
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        with patch('src.billing.models.PaymentMethod') as MockPaymentMethod:
            mock_payment_method_instance = Mock()
            mock_payment_method_instance.id = str(uuid.uuid4())
            MockPaymentMethod.return_value = mock_payment_method_instance
            
            # Act
            result = await payment_processor.add_payment_method(customer_id, payment_method_data)
            
            # Assert
            assert result is not None
            mock_stripe_gateway.add_payment_method.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_invoice_total(self, payment_processor, sample_invoice_data):
        """Test invoice total calculation."""
        # Arrange
        line_items = [
            {"quantity": 2, "unit_price": Decimal("50.00"), "tax_rate": Decimal("0.08")},
            {"quantity": 1, "unit_price": Decimal("100.00"), "tax_rate": Decimal("0.08")},
        ]
        
        # Act
        total = payment_processor._calculate_invoice_total(line_items)
        
        # Assert
        expected_subtotal = Decimal("200.00")  # (2*50 + 1*100)
        expected_tax = Decimal("16.00")  # 200 * 0.08
        expected_total = Decimal("216.00")
        assert total == expected_total

    @pytest.mark.asyncio
    async def test_process_refund_success(self, payment_processor, mock_db_session, mock_stripe_gateway):
        """Test successful payment refund."""
        # Arrange
        payment_id = str(uuid.uuid4())
        refund_amount = Decimal("50.00")
        
        mock_payment = Mock(spec=Payment)
        mock_payment.id = payment_id
        mock_payment.gateway_payment_id = "pi_test_123"
        mock_payment.amount = Decimal("99.99")
        mock_payment.status = PaymentStatus.COMPLETED
        
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        mock_db_session.get = AsyncMock(return_value=mock_payment)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        
        mock_refund_response = {
            "id": "re_test_123",
            "status": "succeeded",
            "amount": int(refund_amount * 100)
        }
        mock_stripe_gateway.process_refund = AsyncMock(return_value=mock_refund_response)
        
        # Act
        result = await payment_processor.process_refund(payment_id, refund_amount, "Customer request")
        
        # Assert
        assert result is not None
        mock_stripe_gateway.process_refund.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_billing_history(self, payment_processor, mock_db_session):
        """Test billing history retrieval."""
        # Arrange
        customer_id = str(uuid.uuid4())
        mock_payments = [Mock(spec=Payment) for _ in range(3)]
        mock_invoices = [Mock(spec=Invoice) for _ in range(2)]
        
        mock_payments_result = Mock()
        mock_payments_result.scalars.return_value.all.return_value = mock_payments
        
        mock_invoices_result = Mock()
        mock_invoices_result.scalars.return_value.all.return_value = mock_invoices
        
        mock_db_session.execute = AsyncMock(side_effect=[mock_payments_result, mock_invoices_result])
        
        # Act
        history = await payment_processor.get_billing_history(customer_id)
        
        # Assert
        assert "payments" in history
        assert "invoices" in history
        assert len(history["payments"]) == 3
        assert len(history["invoices"]) == 2

    @pytest.mark.asyncio
    async def test_generate_billing_report(self, payment_processor, mock_db_session):
        """Test billing report generation."""
        # Arrange
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock revenue data
        mock_revenue_result = Mock()
        mock_revenue_result.fetchone.return_value = (Decimal("5000.00"),)
        
        # Mock payment count data
        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = (25,)
        
        # Mock subscription data
        mock_subscription_result = Mock()
        mock_subscription_result.fetchone.return_value = (15,)
        
        mock_db_session.execute = AsyncMock(side_effect=[
            mock_revenue_result,
            mock_count_result,
            mock_subscription_result
        ])
        
        # Act
        report = await payment_processor.generate_billing_report(start_date, end_date)
        
        # Assert
        assert "total_revenue" in report
        assert "payment_count" in report
        assert "active_subscriptions" in report
        assert report["total_revenue"] == Decimal("5000.00")
        assert report["payment_count"] == 25
        assert report["active_subscriptions"] == 15

    @pytest.mark.asyncio
    async def test_process_recurring_payments(self, payment_processor, mock_db_session):
        """Test recurring payment processing."""
        # Arrange
        mock_subscriptions = [
            Mock(spec=Subscription, id=str(uuid.uuid4()), next_billing_date=datetime.now().date()),
            Mock(spec=Subscription, id=str(uuid.uuid4()), next_billing_date=datetime.now().date())
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_subscriptions
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(payment_processor, '_process_subscription_payment') as mock_process_sub:
            mock_process_sub.return_value = True
            
            # Act
            result = await payment_processor.process_recurring_payments()
            
            # Assert
            assert result["processed_count"] == 2
            assert result["successful_count"] == 2
            assert mock_process_sub.call_count == 2

    @pytest.mark.asyncio
    async def test_update_payment_method_success(self, payment_processor, mock_payment_method, mock_db_session):
        """Test payment method update."""
        # Arrange
        payment_method_id = mock_payment_method.id
        update_data = {"is_default": True, "billing_address": "123 Main St"}
        
        mock_db_session.get = AsyncMock(return_value=mock_payment_method)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await payment_processor.update_payment_method(payment_method_id, update_data)
        
        # Assert
        assert result.is_default == True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_payment_method(self, payment_processor, mock_stripe_gateway):
        """Test payment method validation."""
        # Arrange
        payment_processor.gateways = {"stripe": mock_stripe_gateway}
        payment_method_token = "pm_test_card"
        
        mock_validation_response = {
            "valid": True,
            "card": {"brand": "visa", "last4": "4242"}
        }
        mock_stripe_gateway.validate_payment_method = AsyncMock(return_value=mock_validation_response)
        
        # Act
        result = await payment_processor.validate_payment_method(payment_method_token)
        
        # Assert
        assert result["valid"] is True
        assert result["card"]["brand"] == "visa"
        mock_stripe_gateway.validate_payment_method.assert_called_once_with(payment_method_token)

    @pytest.mark.parametrize("gateway_name,expected_class", [
        ("stripe", "StripePaymentGateway"),
        ("paypal", "PayPalPaymentGateway")
    ])
    def test_get_payment_gateway(self, payment_processor, gateway_name, expected_class):
        """Test payment gateway retrieval."""
        # Arrange
        mock_gateway = Mock()
        mock_gateway.__class__.__name__ = expected_class
        payment_processor.gateways = {gateway_name: mock_gateway}
        
        # Act
        gateway = payment_processor._get_payment_gateway(gateway_name)
        
        # Assert
        assert gateway.__class__.__name__ == expected_class

    @pytest.mark.asyncio
    async def test_handle_payment_webhook_stripe(self, payment_processor, mock_db_session):
        """Test Stripe webhook handling."""
        # Arrange
        webhook_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "status": "succeeded",
                    "amount": 9999,
                    "currency": "usd"
                }
            }
        }
        
        mock_payment = Mock(spec=Payment)
        mock_payment.gateway_payment_id = "pi_test_123"
        mock_payment.status = PaymentStatus.PENDING
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_payment
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await payment_processor.handle_webhook("stripe", webhook_data)
        
        # Assert
        assert result["processed"] is True
        assert mock_payment.status == PaymentStatus.COMPLETED
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_tax_amount(self, payment_processor):
        """Test tax calculation."""
        # Arrange
        subtotal = Decimal("100.00")
        tax_rate = Decimal("0.0875")  # 8.75%
        
        # Act
        tax_amount = payment_processor._calculate_tax_amount(subtotal, tax_rate)
        
        # Assert
        expected_tax = Decimal("8.75")
        assert tax_amount == expected_tax

    @pytest.mark.asyncio
    async def test_send_payment_receipt(self, payment_processor):
        """Test payment receipt sending."""
        # Arrange
        payment_id = str(uuid.uuid4())
        
        with patch('src.notifications.service.NotificationService') as MockNotificationService:
            mock_notification_service = MockNotificationService.return_value
            mock_notification_service.send_payment_receipt = AsyncMock()
            
            # Act
            result = await payment_processor.send_payment_receipt(payment_id)
            
            # Assert
            assert result is True
            mock_notification_service.send_payment_receipt.assert_called_once_with(payment_id)

    @pytest.mark.asyncio
    async def test_get_payment_analytics(self, payment_processor, mock_db_session):
        """Test payment analytics generation."""
        # Arrange
        date_range = (datetime.now() - timedelta(days=30), datetime.now())
        
        # Mock analytics data
        mock_analytics_result = Mock()
        mock_analytics_result.fetchall.return_value = [
            ("2024-01-01", Decimal("1000.00"), 10),
            ("2024-01-02", Decimal("1500.00"), 15),
        ]
        mock_db_session.execute = AsyncMock(return_value=mock_analytics_result)
        
        # Act
        analytics = await payment_processor.get_payment_analytics(date_range)
        
        # Assert
        assert "daily_revenue" in analytics
        assert "daily_transaction_count" in analytics
        assert len(analytics["daily_revenue"]) == 2