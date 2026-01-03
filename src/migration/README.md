# Legal AI System - Complete Data Migration System

A comprehensive, production-ready data migration system for migrating from SQLite databases to PostgreSQL with zero-downtime cutover capabilities.

## 🎯 Overview

This migration system provides:

- **Complete Data Migration**: SQLite → PostgreSQL with schema transformation
- **User & Authentication Migration**: Secure preservation of user accounts, passwords, sessions
- **Document Migration**: File migration with encryption, deduplication, and integrity checks
- **Zero-Downtime Cutover**: Gradual traffic shifting with automated rollback
- **Comprehensive Testing**: Production data copy testing with integrity verification
- **Rollback Capabilities**: Multi-level rollback with checkpoint management

## 📁 System Components

```
src/migration/
├── migrate.py                    # Main migration pipeline
├── user_migration.py            # User & authentication migration
├── document_migration.py        # Document & file migration
├── zero_downtime_cutover.py     # Zero-downtime cutover strategy
├── rollback_manager.py          # Rollback management system
├── test_migration.py            # Comprehensive testing framework
├── migration_config.json        # Configuration template
└── README.md                    # This documentation
```

## 🚀 Quick Start

### 1. Configuration

Create your migration configuration:

```bash
# Create configuration from template
cp src/migration/migration_config.json my_migration_config.json

# Edit configuration with your specific settings
nano my_migration_config.json
```

### 2. Test with Production Data Copy

```bash
# Run comprehensive tests with production data copy
python -m src.migration.test_migration --config my_migration_config.json
```

### 3. Execute Migration

```bash
# Run full migration with zero-downtime cutover
python -m src.migration.migrate --config my_migration_config.json

# Or run dry-run first
python -m src.migration.migrate --config my_migration_config.json --dry-run
```

### 4. Monitor Progress

```bash
# Check migration status
python -m src.migration.migrate --status

# View logs
tail -f migration.log
```

## 📋 Prerequisites

### Infrastructure Requirements

- **Source**: SQLite databases (existing legal-ai-system)
- **Target**: PostgreSQL 12+ database
- **Redis**: For coordination and configuration management
- **Storage**: Sufficient disk space (3x source data size recommended)
- **Network**: Reliable connection between source and target

### Software Dependencies

```bash
# Install Python dependencies
pip install asyncio sqlalchemy asyncpg psycopg2 aioredis
pip install cryptography bcrypt pillow pymupdf python-magic
pip install pytest numpy aiohttp

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install postgresql-client redis-server

# Install system dependencies (macOS)
brew install postgresql redis
```

### Database Setup

```sql
-- Create target PostgreSQL database
CREATE DATABASE legal_ai_production;
CREATE USER legal_ai_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE legal_ai_production TO legal_ai_user;
```

## 🔧 Configuration Guide

### Basic Configuration

```json
{
  "migration_config": {
    "source_databases": {
      "main_cases": "legal_cases.db",
      "auth": "enhanced_auth.db"
    },
    "target_database_url": "postgresql://user:pass@localhost:5432/legal_ai",
    "batch_size": 1000,
    "verify_data": true,
    "zero_downtime": true
  }
}
```

### Advanced Configuration

```json
{
  "user_migration_config": {
    "preserve_passwords": true,
    "encrypt_sensitive_fields": true,
    "migrate_sessions": true
  },
  "document_migration_config": {
    "enable_encryption": true,
    "enable_deduplication": true,
    "max_file_size_mb": 100
  },
  "zero_downtime_cutover_config": {
    "traffic_shift_increments": [10, 25, 50, 75, 90, 100],
    "auto_rollback_enabled": true,
    "error_threshold_percent": 1.0
  }
}
```

## 🧪 Testing Strategy

### 1. Unit Tests

```bash
# Run unit tests
python -m pytest src/migration/test_migration.py -v
```

### 2. Integration Tests

```bash
# Run integration tests with test databases
python -m src.migration.test_migration --integration
```

### 3. Production Data Copy Tests

```bash
# Test with anonymized production data
python -m src.migration.test_migration --production-copy --anonymize
```

### 4. Load Testing

```bash
# Run load tests
python -m src.migration.test_migration --load-test --concurrent-users 100
```

## 🔄 Migration Process

### Phase 1: Preparation

1. **Data Analysis**: Analyze source databases and validate schema
2. **Environment Setup**: Prepare target database and storage
3. **Backup Creation**: Create comprehensive backups
4. **Dependency Check**: Verify all prerequisites

### Phase 2: Data Migration

1. **Schema Migration**: Create PostgreSQL schema from SQLite
2. **Data Migration**: Migrate data with batching and verification
3. **User Migration**: Migrate users with password preservation
4. **Document Migration**: Migrate files with encryption

### Phase 3: Zero-Downtime Cutover

1. **Dual-Write Enablement**: Write to both databases
2. **Traffic Shifting**: Gradually shift read traffic (10% → 100%)
3. **Health Monitoring**: Continuous monitoring and verification
4. **Cutover Completion**: Complete switch to new system

### Phase 4: Verification

1. **Data Integrity**: Verify data consistency and completeness
2. **Application Testing**: Test all critical functionality
3. **Performance Validation**: Ensure performance targets met
4. **User Acceptance**: Verify user experience

## 🛡️ Security Features

### Data Protection

- **Encryption at Rest**: All migrated data encrypted
- **Encryption in Transit**: Secure data transmission
- **Key Management**: Secure encryption key handling
- **Audit Logging**: Complete audit trail

### Access Control

- **Authentication Preservation**: Existing user accounts maintained
- **Permission Migration**: Role-based permissions preserved
- **Session Management**: Active sessions handled gracefully
- **Multi-Factor Support**: MFA settings preserved

## 📊 Monitoring & Alerting

### Real-Time Metrics

- Migration progress and performance
- Error rates and data integrity scores
- System resource utilization
- Health check status

### Alerting

```json
{
  "alert_channels": ["slack", "email"],
  "thresholds": {
    "error_rate": 1.0,
    "data_integrity": 95.0,
    "performance_degradation": 50.0
  }
}
```

### Dashboards

- Migration progress dashboard
- System health dashboard
- Performance metrics dashboard

## 🔄 Rollback Procedures

### Automatic Rollback

Triggers automatic rollback on:
- Health check failures (3 consecutive)
- Error rate > 5%
- Data integrity < 95%
- Critical system errors

### Manual Rollback

```bash
# Execute immediate rollback
python -m src.migration.rollback_manager --execute --reason manual_request

# Rollback to specific checkpoint
python -m src.migration.rollback_manager --checkpoint checkpoint_20241201_143000
```

### Rollback Verification

```bash
# Verify rollback success
python -m src.migration.rollback_manager --verify

# Check rollback status
python -m src.migration.rollback_manager --status
```

## 🎛️ Operation Commands

### Migration Commands

```bash
# Create default configuration
python -m src.migration.migrate --create-config migration_config.json

# Run dry-run migration
python -m src.migration.migrate --config config.json --dry-run

# Execute full migration
python -m src.migration.migrate --config config.json

# Execute verification only
python -m src.migration.migrate --verify-only

# Execute rollback
python -m src.migration.migrate --rollback
```

### Testing Commands

```bash
# Run comprehensive test suite
python -m src.migration.test_migration --config test_config.json

# Run specific test category
python -m src.migration.test_migration --category "data_migration"

# Run performance tests
python -m src.migration.test_migration --performance

# Generate test report
python -m src.migration.test_migration --report-only
```

### Monitoring Commands

```bash
# Check migration status
python -m src.migration.migrate --status

# View performance metrics
python -m src.migration.migrate --metrics

# Export migration report
python -m src.migration.migrate --export-report migration_report.json
```

## 🚨 Troubleshooting

### Common Issues

#### Migration Failures

```bash
# Check detailed logs
tail -f migration.log | grep ERROR

# Verify database connections
python -m src.migration.migrate --test-connections

# Check disk space
df -h
```

#### Performance Issues

```bash
# Monitor resource usage
htop

# Check database performance
python -m src.migration.migrate --performance-check

# Adjust batch size
# Edit config: "batch_size": 500
```

#### Data Integrity Issues

```bash
# Run integrity check
python -m src.migration.migrate --integrity-check

# Compare source vs target
python -m src.migration.migrate --compare-data

# Fix specific table
python -m src.migration.migrate --fix-table table_name
```

### Recovery Procedures

#### Stuck Migration

```bash
# Check migration state
python -m src.migration.migrate --status

# Reset migration state
python -m src.migration.migrate --reset-state

# Resume from checkpoint
python -m src.migration.migrate --resume
```

#### Database Connection Issues

```bash
# Test connections
python -m src.migration.migrate --test-connections

# Reset connection pools
python -m src.migration.migrate --reset-connections

# Use backup database URL
# Edit config with backup URL
```

## 📈 Performance Optimization

### Configuration Tuning

```json
{
  "performance_config": {
    "batch_size": 1000,
    "parallel_workers": 4,
    "connection_pool_size": 20,
    "read_timeout": 30,
    "write_timeout": 60
  }
}
```

### Resource Allocation

- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM for large datasets
- **Storage**: SSD recommended for performance
- **Network**: High bandwidth for large file transfers

### Optimization Tips

1. **Batch Size**: Adjust based on available memory
2. **Parallel Workers**: Match to CPU cores
3. **Connection Pooling**: Optimize pool sizes
4. **Compression**: Enable for large files
5. **Deduplication**: Enable for storage efficiency

## 🔐 Security Best Practices

### Pre-Migration Security

1. **Backup Encryption**: Encrypt all backups
2. **Access Control**: Restrict migration access
3. **Network Security**: Use VPN/SSL connections
4. **Key Management**: Secure encryption keys

### During Migration

1. **Monitoring**: Monitor all migration activities
2. **Audit Logging**: Log all operations
3. **Data Validation**: Verify data integrity
4. **Access Restriction**: Limit system access

### Post-Migration Security

1. **Key Rotation**: Rotate encryption keys
2. **Access Review**: Review user permissions
3. **Security Scan**: Scan for vulnerabilities
4. **Compliance Check**: Verify regulatory compliance

## 📞 Support & Maintenance

### Log Files

- `migration.log` - Main migration log
- `rollback.log` - Rollback operations log
- `performance.log` - Performance metrics log
- `error.log` - Error details log

### Support Information

For migration support:
1. Check logs for detailed error information
2. Run diagnostic commands
3. Review configuration settings
4. Consult troubleshooting guide

### Maintenance Tasks

#### Daily

- Monitor migration progress
- Check error logs
- Verify data integrity
- Review performance metrics

#### Weekly

- Clean up old logs
- Archive completed migrations
- Update security certificates
- Review access permissions

#### Monthly

- Performance optimization review
- Security audit
- Backup verification
- Documentation updates

## 📋 Checklist

### Pre-Migration Checklist

- [ ] PostgreSQL database created and configured
- [ ] Redis server running and accessible
- [ ] Sufficient disk space available (3x source data)
- [ ] Network connectivity verified
- [ ] Backup strategy implemented
- [ ] Configuration file reviewed and validated
- [ ] Test environment prepared
- [ ] Team notifications sent

### Migration Day Checklist

- [ ] Final backup created
- [ ] Migration configuration validated
- [ ] Monitoring systems enabled
- [ ] Support team on standby
- [ ] Communication plan activated
- [ ] Migration executed
- [ ] Progress monitored
- [ ] Verification completed

### Post-Migration Checklist

- [ ] Data integrity verified
- [ ] Application functionality tested
- [ ] Performance benchmarks met
- [ ] User access verified
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Team debriefing completed
- [ ] Lessons learned documented

## 🏆 Success Criteria

### Data Migration Success

- ✅ 100% data migrated without loss
- ✅ Data integrity score > 99.5%
- ✅ All relationships preserved
- ✅ Performance targets met

### User Migration Success

- ✅ All user accounts migrated
- ✅ Authentication working correctly
- ✅ Permissions preserved
- ✅ No user disruption

### System Migration Success

- ✅ Zero downtime achieved
- ✅ All applications functional
- ✅ Performance acceptable
- ✅ Security maintained

---

**🎉 Congratulations!** You now have a complete, production-ready data migration system for your Legal AI System. This comprehensive solution handles everything from initial data migration to zero-downtime cutover with full rollback capabilities.

For additional support or questions, refer to the troubleshooting section or review the detailed logging output.