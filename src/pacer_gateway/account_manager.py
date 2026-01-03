"""
PACER Account Manager

Manages PACER accounts, credentials, and access control.
Handles account rotation, load balancing, and compliance monitoring.
"""

import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging

from ..shared.security.password_manager import password_manager
from ..shared.utils.cache_manager import cache_manager
from .models import (
    PacerAccount, AccountStatus, UsageStatistics, CostAlert,
    CourtInfo, FEDERAL_COURTS
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AccountPool:
    """Pool of PACER accounts for load balancing"""
    pool_id: str
    accounts: List[PacerAccount] = field(default_factory=list)
    current_index: int = 0
    max_concurrent_sessions: int = 5
    active_sessions: Dict[str, datetime] = field(default_factory=dict)  # account_id -> session_start
    
    def get_next_account(self, court_id: str = None) -> Optional[PacerAccount]:
        """Get next available account using round-robin"""
        available_accounts = [
            acc for acc in self.accounts 
            if acc.is_active() and (not court_id or acc.can_access_court(court_id))
        ]
        
        if not available_accounts:
            return None
        
        # Simple round-robin selection
        account = available_accounts[self.current_index % len(available_accounts)]
        self.current_index = (self.current_index + 1) % len(available_accounts)
        
        return account
    
    def get_least_used_account(self, court_id: str = None) -> Optional[PacerAccount]:
        """Get account with least recent usage"""
        available_accounts = [
            acc for acc in self.accounts 
            if acc.is_active() and (not court_id or acc.can_access_court(court_id))
        ]
        
        if not available_accounts:
            return None
        
        # Sort by last used time (None = never used = highest priority)
        sorted_accounts = sorted(
            available_accounts, 
            key=lambda x: x.last_used_at or datetime.min.replace(tzinfo=timezone.utc)
        )
        
        return sorted_accounts[0]
    
    def mark_account_used(self, account_id: str):
        """Mark account as recently used"""
        self.active_sessions[account_id] = datetime.now(timezone.utc)
        
        # Update account's last used time
        for account in self.accounts:
            if account.account_id == account_id:
                account.last_used_at = datetime.now(timezone.utc)
                break
    
    def release_account(self, account_id: str):
        """Release account from active use"""
        self.active_sessions.pop(account_id, None)
    
    def get_available_capacity(self) -> int:
        """Get number of available concurrent sessions"""
        active_count = len(self.active_sessions)
        return max(0, self.max_concurrent_sessions - active_count)


class PacerAccountManager:
    """Centralized PACER account management"""
    
    def __init__(self):
        self.account_pools: Dict[str, AccountPool] = {}
        self.accounts: Dict[str, PacerAccount] = {}
        self.usage_stats: Dict[str, List[UsageStatistics]] = {}
        self.cost_alerts: Dict[str, List[CostAlert]] = {}
        
        # Default account pool
        self.default_pool = AccountPool("default")
        self.account_pools["default"] = self.default_pool
        
        # Account rotation settings
        self.max_requests_per_account_per_hour = 100
        self.max_cost_per_account_per_day = 10000  # $100.00 in cents
        self.session_timeout_minutes = 240  # 4 hours
        
        logger.info("PACER Account Manager initialized")
    
    async def add_account(
        self,
        username: str,
        password: str,
        client_code: str,
        daily_limit_dollars: float = 100.0,
        monthly_limit_dollars: float = 3000.0,
        allowed_courts: List[str] = None,
        pool_name: str = "default"
    ) -> PacerAccount:
        """Add a new PACER account"""
        
        try:
            # Generate unique account ID
            account_id = f"pacer_{secrets.token_hex(8)}"
            
            # Encrypt password
            encrypted_password = password_manager.hash_password(password)
            
            # Create account
            account = PacerAccount(
                account_id=account_id,
                username=username,
                password=encrypted_password,
                client_code=client_code,
                daily_limit_dollars=daily_limit_dollars,
                monthly_limit_dollars=monthly_limit_dollars,
                allowed_courts=allowed_courts or [],
                status=AccountStatus.ACTIVE
            )
            
            # Add to storage
            self.accounts[account_id] = account
            
            # Add to pool
            if pool_name not in self.account_pools:
                self.account_pools[pool_name] = AccountPool(pool_name)
            
            self.account_pools[pool_name].accounts.append(account)
            
            # Initialize usage tracking
            self.usage_stats[account_id] = []
            self.cost_alerts[account_id] = []
            
            # Cache account info
            await cache_manager.set(
                f"pacer:account:{account_id}",
                account.__dict__,
                ttl=3600
            )
            
            logger.info(f"Added PACER account {username} to pool {pool_name}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to add PACER account: {str(e)}")
            raise
    
    async def remove_account(self, account_id: str) -> bool:
        """Remove a PACER account"""
        
        try:
            if account_id not in self.accounts:
                return False
            
            account = self.accounts[account_id]
            
            # Remove from all pools
            for pool in self.account_pools.values():
                pool.accounts = [acc for acc in pool.accounts if acc.account_id != account_id]
            
            # Remove from storage
            del self.accounts[account_id]
            
            # Clean up tracking data
            self.usage_stats.pop(account_id, None)
            self.cost_alerts.pop(account_id, None)
            
            # Remove from cache
            await cache_manager.delete(f"pacer:account:{account_id}")
            
            logger.info(f"Removed PACER account {account.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove PACER account: {str(e)}")
            return False
    
    async def get_account(self, account_id: str) -> Optional[PacerAccount]:
        """Get account by ID"""
        
        # Try cache first
        cached_account = await cache_manager.get(f"pacer:account:{account_id}")
        if cached_account:
            return PacerAccount(**cached_account)
        
        # Fallback to memory
        account = self.accounts.get(account_id)
        if account:
            # Update cache
            await cache_manager.set(
                f"pacer:account:{account_id}",
                account.__dict__,
                ttl=3600
            )
        
        return account
    
    async def get_available_account(
        self,
        court_id: str = None,
        pool_name: str = "default",
        selection_strategy: str = "round_robin"
    ) -> Optional[Tuple[PacerAccount, str]]:
        """Get an available account for use"""
        
        try:
            pool = self.account_pools.get(pool_name)
            if not pool:
                logger.warning(f"Account pool {pool_name} not found")
                return None
            
            # Check pool capacity
            if pool.get_available_capacity() <= 0:
                logger.warning(f"Account pool {pool_name} at capacity")
                return None
            
            # Select account based on strategy
            if selection_strategy == "least_used":
                account = pool.get_least_used_account(court_id)
            else:  # round_robin (default)
                account = pool.get_next_account(court_id)
            
            if not account:
                logger.warning(f"No available accounts in pool {pool_name} for court {court_id}")
                return None
            
            # Check account limits
            if not await self._check_account_limits(account):
                logger.warning(f"Account {account.username} has exceeded limits")
                return None
            
            # Mark account as in use
            pool.mark_account_used(account.account_id)
            
            logger.info(f"Allocated account {account.username} for court {court_id}")
            return account, pool_name
            
        except Exception as e:
            logger.error(f"Failed to get available account: {str(e)}")
            return None
    
    async def release_account(self, account_id: str, pool_name: str = "default"):
        """Release an account back to the pool"""
        
        try:
            pool = self.account_pools.get(pool_name)
            if pool:
                pool.release_account(account_id)
                logger.debug(f"Released account {account_id} from pool {pool_name}")
            
        except Exception as e:
            logger.error(f"Failed to release account: {str(e)}")
    
    async def update_account_status(
        self,
        account_id: str,
        status: AccountStatus,
        reason: str = ""
    ) -> bool:
        """Update account status"""
        
        try:
            account = await self.get_account(account_id)
            if not account:
                return False
            
            old_status = account.status
            account.status = status
            
            # Update in storage
            self.accounts[account_id] = account
            
            # Update cache
            await cache_manager.set(
                f"pacer:account:{account_id}",
                account.__dict__,
                ttl=3600
            )
            
            logger.info(
                f"Updated account {account.username} status: {old_status.value} -> {status.value}"
                f"{f' ({reason})' if reason else ''}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update account status: {str(e)}")
            return False
    
    async def track_usage(
        self,
        account_id: str,
        court_id: str,
        request_type: str,
        cost_cents: int = 0,
        page_count: int = 0,
        document_count: int = 0,
        response_time_ms: float = 0.0
    ):
        """Track account usage for monitoring and billing"""
        
        try:
            account = await self.get_account(account_id)
            if not account:
                return
            
            today = datetime.now(timezone.utc).date()
            
            # Find or create today's usage stats
            today_stats = None
            account_usage = self.usage_stats.get(account_id, [])
            
            for stats in account_usage:
                if stats.date.date() == today:
                    today_stats = stats
                    break
            
            if not today_stats:
                today_stats = UsageStatistics(
                    account_id=account_id,
                    date=datetime.now(timezone.utc)
                )
                account_usage.append(today_stats)
                self.usage_stats[account_id] = account_usage
            
            # Update stats
            today_stats.total_requests += 1
            today_stats.successful_requests += 1  # Assume success unless error tracking added
            today_stats.total_cost_cents += cost_cents
            today_stats.total_pages += page_count
            today_stats.total_documents += document_count
            
            if court_id and court_id not in today_stats.courts_accessed:
                today_stats.courts_accessed.append(court_id)
                today_stats.unique_cases_accessed += 1  # Simplified
            
            # Update response time average
            if response_time_ms > 0:
                current_avg = today_stats.average_response_time_ms
                total_requests = today_stats.total_requests
                
                today_stats.average_response_time_ms = (
                    (current_avg * (total_requests - 1) + response_time_ms) / total_requests
                )
            
            # Check cost alerts
            await self._check_cost_alerts(account_id, today_stats)
            
            logger.debug(f"Tracked usage for account {account.username}: ${cost_cents/100:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to track usage: {str(e)}")
    
    async def get_usage_statistics(
        self,
        account_id: str,
        days: int = 30
    ) -> List[UsageStatistics]:
        """Get usage statistics for an account"""
        
        try:
            account_usage = self.usage_stats.get(account_id, [])
            
            # Filter by date range
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            filtered_stats = [
                stats for stats in account_usage
                if stats.date >= cutoff_date
            ]
            
            # Sort by date (newest first)
            filtered_stats.sort(key=lambda x: x.date, reverse=True)
            
            return filtered_stats
            
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {str(e)}")
            return []
    
    async def add_cost_alert(
        self,
        account_id: str,
        alert_type: str,
        threshold_dollars: float,
        notification_email: str = None,
        auto_suspend: bool = False
    ) -> Optional[CostAlert]:
        """Add cost alert for an account"""
        
        try:
            alert_id = f"alert_{secrets.token_hex(8)}"
            
            alert = CostAlert(
                alert_id=alert_id,
                account_id=account_id,
                alert_type=alert_type,
                threshold_cents=int(threshold_dollars * 100),
                notification_email=notification_email,
                auto_suspend=auto_suspend
            )
            
            if account_id not in self.cost_alerts:
                self.cost_alerts[account_id] = []
            
            self.cost_alerts[account_id].append(alert)
            
            logger.info(
                f"Added cost alert for account {account_id}: "
                f"{alert_type} threshold ${threshold_dollars:.2f}"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to add cost alert: {str(e)}")
            return None
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        
        try:
            account = await self.get_account(account_id)
            if not account:
                return {}
            
            # Get recent usage stats
            recent_stats = await self.get_usage_statistics(account_id, days=7)
            
            # Calculate totals
            total_cost_cents = sum(stats.total_cost_cents for stats in recent_stats)
            total_requests = sum(stats.total_requests for stats in recent_stats)
            total_pages = sum(stats.total_pages for stats in recent_stats)
            
            # Get active alerts
            active_alerts = [
                alert for alert in self.cost_alerts.get(account_id, [])
                if alert.is_active
            ]
            
            return {
                'account_id': account_id,
                'username': account.username,
                'status': account.status.value,
                'created_at': account.created_at.isoformat(),
                'last_used_at': account.last_used_at.isoformat() if account.last_used_at else None,
                'daily_limit_dollars': account.daily_limit_dollars,
                'monthly_limit_dollars': account.monthly_limit_dollars,
                'allowed_courts': account.allowed_courts,
                'usage_last_7_days': {
                    'total_cost_dollars': total_cost_cents / 100.0,
                    'total_requests': total_requests,
                    'total_pages': total_pages,
                    'average_cost_per_request': total_cost_cents / max(1, total_requests) / 100.0
                },
                'active_alerts': len(active_alerts),
                'recent_stats_count': len(recent_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get account summary: {str(e)}")
            return {}
    
    async def get_pool_status(self, pool_name: str = "default") -> Dict[str, Any]:
        """Get pool status and statistics"""
        
        try:
            pool = self.account_pools.get(pool_name)
            if not pool:
                return {}
            
            active_accounts = [acc for acc in pool.accounts if acc.is_active()]
            
            return {
                'pool_id': pool.pool_id,
                'total_accounts': len(pool.accounts),
                'active_accounts': len(active_accounts),
                'available_capacity': pool.get_available_capacity(),
                'max_concurrent_sessions': pool.max_concurrent_sessions,
                'current_active_sessions': len(pool.active_sessions),
                'accounts': [
                    {
                        'account_id': acc.account_id,
                        'username': acc.username,
                        'status': acc.status.value,
                        'last_used': acc.last_used_at.isoformat() if acc.last_used_at else None
                    }
                    for acc in active_accounts
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get pool status: {str(e)}")
            return {}
    
    async def _check_account_limits(self, account: PacerAccount) -> bool:
        """Check if account is within usage limits"""
        
        try:
            # Get today's usage
            today_stats = None
            account_usage = self.usage_stats.get(account.account_id, [])
            today = datetime.now(timezone.utc).date()
            
            for stats in account_usage:
                if stats.date.date() == today:
                    today_stats = stats
                    break
            
            if today_stats:
                # Check daily cost limit
                daily_cost_dollars = today_stats.total_cost_dollars
                if daily_cost_dollars >= account.daily_limit_dollars:
                    logger.warning(
                        f"Account {account.username} exceeded daily limit: "
                        f"${daily_cost_dollars:.2f} >= ${account.daily_limit_dollars:.2f}"
                    )
                    return False
                
                # Check hourly request limit
                if today_stats.total_requests >= account.rate_limit_per_hour:
                    logger.warning(
                        f"Account {account.username} exceeded hourly request limit: "
                        f"{today_stats.total_requests} >= {account.rate_limit_per_hour}"
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check account limits: {str(e)}")
            return False
    
    async def _check_cost_alerts(self, account_id: str, usage_stats: UsageStatistics):
        """Check and trigger cost alerts"""
        
        try:
            alerts = self.cost_alerts.get(account_id, [])
            
            for alert in alerts:
                if not alert.is_active or alert.is_triggered:
                    continue
                
                # Check threshold based on alert type
                current_amount = 0
                
                if alert.alert_type == "daily":
                    current_amount = usage_stats.total_cost_cents
                elif alert.alert_type == "monthly":
                    # Calculate monthly total (simplified)
                    monthly_stats = self.usage_stats.get(account_id, [])
                    this_month = datetime.now(timezone.utc).replace(day=1)
                    
                    monthly_total = sum(
                        stats.total_cost_cents for stats in monthly_stats
                        if stats.date >= this_month
                    )
                    current_amount = monthly_total
                
                # Update current amount
                alert.current_amount_cents = current_amount
                
                # Check threshold
                if alert.check_threshold():
                    alert.is_triggered = True
                    alert.last_triggered_at = datetime.now(timezone.utc)
                    
                    logger.warning(
                        f"Cost alert triggered for account {account_id}: "
                        f"{alert.alert_type} threshold ${alert.threshold_dollars:.2f} exceeded "
                        f"(current: ${alert.current_amount_dollars:.2f})"
                    )
                    
                    # Auto-suspend if configured
                    if alert.auto_suspend:
                        await self.update_account_status(
                            account_id,
                            AccountStatus.SUSPENDED,
                            f"Auto-suspended due to {alert.alert_type} cost threshold"
                        )
                    
                    # Send notification (implement notification service)
                    if alert.notification_email:
                        # TODO: Implement email notification
                        pass
            
        except Exception as e:
            logger.error(f"Failed to check cost alerts: {str(e)}")


# Global account manager instance
account_manager = PacerAccountManager()