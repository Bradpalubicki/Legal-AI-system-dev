---
# Incident Response Plan
## Legal AI System - Security Incident Management

**Version**: 1.0
**Last Updated**: 2024-01-15
**Review Frequency**: Quarterly
**Classification**: Internal - Confidential

---

## Table of Contents

1. [Overview](#overview)
2. [Incident Classification](#incident-classification)
3. [Response Team](#response-team)
4. [Incident Response Phases](#incident-response-phases)
5. [Incident Playbooks](#incident-playbooks)
6. [Communication Procedures](#communication-procedures)
7. [Post-Incident Activities](#post-incident-activities)
8. [Appendices](#appendices)

---

## Overview

### Purpose

This Incident Response Plan defines procedures for detecting, responding to, and recovering from security incidents affecting the Legal AI System. It ensures rapid response, minimizes damage, and maintains compliance with legal and regulatory requirements.

### Scope

This plan covers:
- **Security breaches** (unauthorized access, data exfiltration)
- **Malware incidents** (ransomware, viruses, trojans)
- **DDoS attacks** (denial of service)
- **Data loss events** (accidental deletion, corruption)
- **System compromises** (account takeovers, privilege escalation)
- **Compliance violations** (GDPR breaches, unauthorized data sharing)

### Compliance Requirements

- **GDPR Article 33**: Breach notification within 72 hours
- **CCPA Section 1798.150**: Data breach liability and notification
- **SOC 2**: Security incident management
- **PCI DSS** (if applicable): Incident response procedures
- **HIPAA** (if applicable): Security incident procedures

### Objectives

- **Rapid Detection**: Identify incidents within minutes
- **Swift Containment**: Stop spread within 1 hour
- **Effective Eradication**: Remove threat within 4 hours
- **Full Recovery**: Restore services within 24 hours
- **Comprehensive Documentation**: Complete incident record
- **Continuous Improvement**: Learn from every incident

---

## Incident Classification

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P0 - Critical** | Complete service outage or active data breach | 15 minutes | Database compromise, active ransomware, data exfiltration |
| **P1 - High** | Partial service disruption or confirmed intrusion | 1 hour | Compromised admin account, malware detected, DDoS attack |
| **P2 - Medium** | Potential security issue or service degradation | 4 hours | Suspicious activity, failed security controls, vulnerability discovered |
| **P3 - Low** | Minor security concern or policy violation | 24 hours | Phishing attempt, minor misconfigurations, audit findings |

### Incident Types

#### Type 1: Unauthorized Access
- Account compromise
- Privilege escalation
- Insider threat
- Physical security breach

**Indicators**:
- Failed login spikes
- Login from unusual locations
- Access outside normal hours
- Multiple account accesses from same IP

#### Type 2: Malware
- Ransomware
- Viruses
- Trojans
- Rootkits
- Cryptominers

**Indicators**:
- Antivirus alerts
- Unusual CPU/network activity
- Files encrypted
- Unknown processes running

#### Type 3: Data Breach
- Data exfiltration
- Unauthorized data access
- Data loss
- Privacy violation

**Indicators**:
- Large data downloads
- Database dumps
- Unusual queries
- GDPR request spike

#### Type 4: Denial of Service
- DDoS attacks
- Resource exhaustion
- Application-level DoS

**Indicators**:
- Traffic spikes
- Service timeouts
- High CPU/memory usage
- Connection exhaustion

#### Type 5: System Compromise
- Server takeover
- Container escape
- Database injection
- Code injection

**Indicators**:
- Modified system files
- Unknown user accounts
- Backdoor detection
- Privilege changes

---

## Response Team

### Incident Response Team (IRT)

**Incident Commander** (IC)
- **Role**: Overall incident coordination
- **Name**: [CTO Name]
- **Primary**: +1-555-0101
- **Email**: cto@legal-ai.com
- **Responsibilities**:
  - Declare incident level
  - Coordinate response team
  - Make critical decisions
  - Communicate with executives
  - Authorize containment actions

**Technical Lead** (TL)
- **Role**: Technical investigation and remediation
- **Name**: [Principal Engineer Name]
- **Primary**: +1-555-0102
- **Email**: principal@legal-ai.com
- **Responsibilities**:
  - Technical analysis
  - Execute containment
  - Coordinate engineers
  - Implement fixes

**Security Lead** (SL)
- **Role**: Security analysis and forensics
- **Name**: [Security Engineer Name]
- **Primary**: +1-555-0103
- **Email**: security@legal-ai.com
- **Responsibilities**:
  - Threat analysis
  - Forensic investigation
  - Evidence preservation
  - Security recommendations

**Communications Lead** (CL)
- **Role**: Internal and external communications
- **Name**: [Communications Manager Name]
- **Primary**: +1-555-0104
- **Email**: comms@legal-ai.com
- **Responsibilities**:
  - Stakeholder notifications
  - Customer communications
  - Regulatory notifications
  - Media relations

**Legal Counsel** (LC)
- **Role**: Legal and regulatory guidance
- **Name**: [Legal Counsel Name]
- **Primary**: +1-555-0105
- **Email**: legal@legal-ai.com
- **Responsibilities**:
  - Legal implications
  - Regulatory compliance
  - Contract review
  - Liability assessment

### On-Call Rotation

**Primary On-Call**:
- Week of Jan 15: Engineer A (+1-555-0110)
- Week of Jan 22: Engineer B (+1-555-0111)
- Week of Jan 29: Engineer C (+1-555-0112)

**Secondary On-Call**:
- Engineer D (+1-555-0113)
- Engineer E (+1-555-0114)

### Escalation Path

```
Monitoring Alert
    ↓
On-Call Engineer (15 min)
    ↓
Technical Lead (30 min)
    ↓
Incident Commander (1 hour)
    ↓
Executive Team (2 hours)
    ↓
Board of Directors (4 hours, if P0)
```

---

## Incident Response Phases

### Phase 1: Preparation

**Ongoing Activities**:
- Maintain incident response tools
- Conduct regular training
- Test backup and recovery
- Review and update procedures
- Monitor threat intelligence

**Readiness Checklist**:
- [ ] Team contact list updated
- [ ] Incident response tools accessible
- [ ] Backup systems tested (monthly)
- [ ] Forensic tools available
- [ ] Communication templates ready
- [ ] Legal counsel identified
- [ ] Regulatory requirements documented

### Phase 2: Detection & Analysis

**Detection Sources**:
1. **Automated Monitoring**
   - IDS/IPS alerts
   - SIEM alerts
   - Antivirus notifications
   - Log analysis
   - Anomaly detection

2. **Manual Discovery**
   - User reports
   - IT staff observations
   - Third-party notifications
   - Audit findings

**Initial Analysis Steps**:

```bash
# 1. Verify the incident
# Check monitoring dashboards
# Review relevant logs
# Confirm indicators

# 2. Classify severity
# Determine impact
# Assess scope
# Estimate affected systems

# 3. Initiate response
# Page on-call team
# Create incident ticket
# Start documentation
```

**Analysis Questions**:
- What happened?
- When did it start?
- How was it discovered?
- What systems are affected?
- Is it still ongoing?
- What data is at risk?
- Who is the attacker (if known)?

### Phase 3: Containment

**Short-Term Containment** (Immediate)

**For Compromised Account**:
```bash
# 1. Disable compromised account
mysql> UPDATE users SET is_active = FALSE WHERE id = <user_id>;

# 2. Revoke all sessions
redis-cli DEL "session:user:<user_id>:*"

# 3. Reset password
# Force password reset on next login

# 4. Review account activity
SELECT * FROM audit_logs WHERE user_id = <user_id>
ORDER BY created_at DESC LIMIT 100;
```

**For Malware Detection**:
```bash
# 1. Isolate infected system
# Disconnect from network (keep powered on for forensics)
iptables -A INPUT -j DROP
iptables -A OUTPUT -j DROP

# 2. Stop malicious processes
ps aux | grep <suspicious_process>
kill -9 <PID>

# 3. Preserve evidence
# Create disk image before cleanup
dd if=/dev/sda of=/mnt/forensics/disk_image.dd bs=4M

# 4. Block command & control
# Add C2 servers to firewall blocklist
```

**For Data Breach**:
```bash
# 1. Identify exfiltration path
# Review network logs, database queries

# 2. Close the gap
# Patch vulnerability
# Block attacker IP

# 3. Assess data exposure
# Determine what data was accessed
# Count affected records

# 4. Preserve audit trail
# Backup all relevant logs
```

**For DDoS Attack**:
```bash
# 1. Enable DDoS protection
# CloudFlare: Enable "I'm Under Attack" mode
# AWS: Enable AWS Shield

# 2. Analyze traffic
# Identify attack vectors
# Determine attack patterns

# 3. Filter malicious traffic
# Update WAF rules
# Add rate limiting

# 4. Scale infrastructure
# Increase instance count
# Enable auto-scaling
```

**Long-Term Containment**

- Deploy patches
- Update firewall rules
- Implement additional monitoring
- Review and revoke credentials
- Segment network if needed

### Phase 4: Eradication

**Remove the Threat**:

```bash
# 1. Patch vulnerabilities
# Apply security updates
apt-get update && apt-get upgrade

# 2. Remove malware
# Use antivirus/anti-malware tools
# Manual removal if needed

# 3. Rebuild compromised systems
# Restore from known-good backups
# Reinstall from trusted sources

# 4. Update credentials
# Reset all potentially compromised passwords
# Rotate API keys, tokens, certificates

# 5. Harden systems
# Implement additional security controls
# Update security policies
```

**Verification**:
- Scan for remaining threats
- Verify vulnerabilities patched
- Confirm malware removed
- Test security controls

### Phase 5: Recovery

**Restore Operations**:

```bash
# 1. Restore from backup (if needed)
/infrastructure/backup/backup_restore.sh restore <backup_file>

# 2. Verify data integrity
# Check database consistency
# Verify file checksums

# 3. Restart services
kubectl rollout restart deployment/legal-ai-api
kubectl rollout restart deployment/legal-ai-frontend

# 4. Monitor closely
# Watch for anomalies
# Check for re-infection

# 5. Gradual restoration
# Restore non-critical systems first
# Monitor each step
# Restore critical systems last
```

**Recovery Checklist**:
- [ ] All malware removed
- [ ] Vulnerabilities patched
- [ ] Credentials rotated
- [ ] Backups verified
- [ ] Services restored
- [ ] Monitoring enhanced
- [ ] Users notified
- [ ] Normal operations confirmed

### Phase 6: Post-Incident Activity

**Immediate Post-Incident** (Within 24 hours):

1. **Preserve Evidence**
   - Secure all logs
   - Document timeline
   - Save forensic images
   - Collect all communications

2. **Preliminary Report**
   - Incident summary
   - Impact assessment
   - Immediate actions taken
   - Estimated cost

3. **Stakeholder Notification**
   - Internal teams
   - Affected customers
   - Regulatory bodies (if required)
   - Law enforcement (if criminal)

**Post-Incident Review** (Within 1 week):

Schedule PIR (Post-Incident Review) meeting with:
- Incident Response Team
- Affected department leads
- Executive sponsor

**PIR Agenda**:
1. What happened? (Timeline)
2. What went well?
3. What could be improved?
4. What did we learn?
5. What actions will we take?

**Lessons Learned Report**:
- Incident summary
- Root cause analysis
- Response effectiveness
- Areas for improvement
- Action items with owners
- Process updates needed

---

## Incident Playbooks

### Playbook 1: Ransomware Attack

**Detection**:
- Files encrypted
- Ransom note displayed
- Antivirus alert
- User reports

**Immediate Actions**:
```bash
# 1. Isolate infected systems (within 5 minutes)
for server in $(cat infected_servers.txt); do
    ssh $server "iptables -A INPUT -j DROP; iptables -A OUTPUT -j DROP"
done

# 2. Identify ransomware variant
# Check ransom note for indicators
# Submit sample to VirusTotal

# 3. Assess spread
# Check for lateral movement
# Identify patient zero

# 4. Stop backups (prevent backup infection)
# Disable automated backup jobs temporarily

# 5. Notify team
# Page Incident Commander
# Assemble response team
```

**DO NOT**:
- ❌ Pay ransom (consult legal first)
- ❌ Delete infected files (evidence)
- ❌ Reboot servers (loses memory forensics)

**Recovery**:
```bash
# 1. Restore from clean backup
# Verify backup is pre-infection
/infrastructure/backup/backup_restore.sh restore <pre_infection_backup>

# 2. Rebuild infected systems
# Complete OS reinstall
# Restore only clean data

# 3. Deploy decryption tool (if available)
# Check nomoreransom.org
# Use vendor-specific tools
```

**Notification Requirements**:
- Law enforcement (FBI, local police)
- Cyber insurance provider
- Affected customers
- Regulatory bodies (within 72 hours)

### Playbook 2: Data Breach

**Detection**:
- Unauthorized database access
- Large data export
- Security alert
- Third-party notification

**Immediate Actions**:
```bash
# 1. Stop the bleeding (within 15 minutes)
# Block attacker IP
iptables -A INPUT -s <attacker_ip> -j DROP

# Revoke compromised credentials
# Patch vulnerability

# 2. Assess scope (within 1 hour)
# Query audit logs
SELECT * FROM audit_logs
WHERE event_type IN ('DATA_READ', 'DATA_EXPORTED')
AND created_at > '<incident_start_time>'
AND ip_address = '<suspicious_ip>';

# Count affected records
SELECT COUNT(*) FROM <affected_table>
WHERE <breach_criteria>;

# 3. Preserve evidence
# Backup all logs
# Save network captures
# Document timeline

# 4. Secure perimeter
# Review all access controls
# Audit user permissions
# Check for other compromises
```

**GDPR Requirements** (if EU data affected):
```bash
# Within 72 hours:
# 1. Notify supervisory authority
# Complete GDPR breach notification form

# 2. Document:
# - Nature of breach
# - Categories of data
# - Number of affected individuals
# - Likely consequences
# - Measures taken

# Without undue delay:
# 3. Notify affected individuals (if high risk)
# Provide clear, plain language notification
# Include recommendations (password change, etc.)
```

**Data Breach Notification Template**:
```
Subject: Important Security Notice - Data Breach

Dear [Customer],

We are writing to inform you of a data security incident affecting your account.

What Happened:
On [date], we discovered unauthorized access to our systems. The incident
involved [description].

What Information Was Involved:
[List data types: names, emails, etc.]
[Do NOT include: passwords, financial data - unless affected]

What We Are Doing:
- Secured our systems
- Engaged cybersecurity experts
- Notified law enforcement
- Enhanced security controls

What You Can Do:
- Change your password immediately
- Enable two-factor authentication
- Monitor your accounts
- Be alert for phishing emails

We sincerely apologize for this incident and any concern it may cause.

For questions: privacy@legal-ai.com or 1-800-XXX-XXXX

Sincerely,
[Name], CEO
Legal AI System
```

### Playbook 3: Compromised Admin Account

**Detection**:
- Unusual admin activity
- Login from unexpected location
- Permission changes
- Security alert

**Immediate Actions**:
```bash
# 1. Disable account (immediately)
UPDATE users SET is_active = FALSE, account_locked_until = NOW() + INTERVAL '24 hours'
WHERE id = <admin_id>;

# 2. Revoke all sessions
DELETE FROM sessions WHERE user_id = <admin_id>;

# 3. Audit recent actions
SELECT * FROM audit_logs
WHERE user_id = <admin_id>
AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

# 4. Check for persistence mechanisms
# Look for new admin accounts
SELECT * FROM users WHERE is_admin = TRUE AND created_at > NOW() - INTERVAL '7 days';

# Look for modified permissions
SELECT * FROM audit_logs WHERE event_type = 'PERMISSION_CHANGED'
AND created_at > <incident_start>;

# 5. Review created/modified resources
SELECT * FROM audit_logs
WHERE user_id = <admin_id>
AND action IN ('create', 'update', 'delete')
AND created_at > <incident_start>;
```

**Recovery**:
```bash
# 1. Revert unauthorized changes
# Based on audit log review

# 2. Remove any backdoors
# Delete unauthorized accounts
# Reset compromised credentials

# 3. Investigate root cause
# How was account compromised?
# Phishing? Password reuse? Malware?

# 4. Strengthen admin security
# Require MFA for all admins
# Implement admin access logging
# Review least privilege
```

### Playbook 4: DDoS Attack

**Detection**:
- Traffic spike
- Service unavailability
- High bandwidth usage
- Customer complaints

**Immediate Actions**:
```bash
# 1. Enable DDoS protection (within 5 minutes)
# CloudFlare
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/<zone_id>/settings/security_level" \
  -H "Authorization: Bearer <token>" \
  -d '{"value":"under_attack"}'

# AWS Shield
aws shield create-protection --name legal-ai-ddos-protection --resource-arn <alb_arn>

# 2. Analyze attack
# Check traffic patterns
# Identify attack vectors (SYN flood, HTTP flood, etc.)

# 3. Filter malicious traffic
# Update WAF rules
# Add rate limiting

# 4. Scale infrastructure
kubectl scale deployment/legal-ai-api --replicas=10

# 5. Contact CDN/hosting provider
# Request DDoS mitigation assistance
```

**Mitigation**:
- Enable geo-blocking (if applicable)
- Implement CAPTCHA
- Cache everything possible
- Null-route attack traffic

---

## Communication Procedures

### Internal Communication

**Incident Declared**:
1. Create Slack channel: `#incident-YYYYMMDD-HH`
2. Page on-call team via PagerDuty
3. Send initial notification email
4. Schedule war room call

**Status Updates**:
- **P0**: Every 30 minutes
- **P1**: Every hour
- **P2**: Every 4 hours
- **P3**: Daily

**Update Template**:
```
INCIDENT STATUS UPDATE - [P-Level]

Incident: [Brief description]
Status: [Ongoing/Contained/Resolved]
Affected: [Services/data/users]
Impact: [Description]
Actions Taken:
- [Action 1]
- [Action 2]
Next Steps:
- [Next action 1]
- [Next action 2]
ETA to Resolution: [Time]

IC: [Name]
Last Updated: [Timestamp]
```

### External Communication

**Customer Notification** (if service impacted):
```
SUBJECT: Service Status Update

We are currently experiencing [issue description]. Our team is
actively working to resolve this issue.

Status: [Investigating/Identified/Monitoring/Resolved]
Affected: [Specific services]
Workaround: [If available]

We will provide updates every [frequency].

For updates: https://status.legal-ai.com
For questions: support@legal-ai.com

We apologize for any inconvenience.
```

**Regulatory Notification** (data breach):
- **EU (GDPR)**: Notify Data Protection Authority within 72 hours
- **California (CCPA)**: Notify Attorney General if >500 CA residents
- **Other states**: Follow state-specific breach laws

**Law Enforcement** (criminal activity):
- FBI Cyber Division: https://www.fbi.gov/investigate/cyber
- IC3 (Internet Crime Complaint Center): https://www.ic3.gov/
- Local law enforcement

---

## Post-Incident Activities

### Evidence Preservation

**What to Preserve**:
- All system logs
- Network captures
- Disk images
- Memory dumps
- Screenshots
- Email communications
- Chat logs

**How to Preserve**:
```bash
# 1. Collect logs
tar -czf incident_logs_$(date +%Y%m%d).tar.gz /var/log/

# 2. Create disk image
dd if=/dev/sda of=/mnt/forensics/disk_$(hostname)_$(date +%Y%m%d).img bs=4M

# 3. Save to secure storage
# Upload to incident evidence S3 bucket
aws s3 cp incident_logs.tar.gz s3://legal-ai-incident-evidence/ --sse AES256
```

**Chain of Custody**:
- Document who collected evidence
- When it was collected
- Where it's stored
- Who has accessed it

### Post-Incident Review

**PIR Meeting Agenda**:
1. **Incident Overview** (10 min)
   - What happened
   - Timeline
   - Impact

2. **Response Analysis** (20 min)
   - What went well
   - What didn't go well
   - Detection time
   - Response time
   - Communication effectiveness

3. **Root Cause** (15 min)
   - How did this happen
   - Why wasn't it prevented
   - Why wasn't it detected sooner

4. **Action Items** (15 min)
   - Immediate fixes
   - Long-term improvements
   - Process changes
   - Training needs

**Action Item Tracking**:
- Assign owner
- Set deadline
- Track in project management tool
- Review in next PIR

### Metrics to Track

- **MTTD** (Mean Time To Detect)
- **MTTA** (Mean Time To Acknowledge)
- **MTTR** (Mean Time To Resolve)
- **Incident Count** by severity
- **False Positive Rate**
- **Cost of Incident**

---

## Appendices

### Appendix A: Contact List

**Internal**:
```
Incident Commander: +1-555-0101
Technical Lead: +1-555-0102
Security Lead: +1-555-0103
Communications Lead: +1-555-0104
Legal Counsel: +1-555-0105
CEO: +1-555-0100

On-Call Primary: +1-555-ONCALL
PagerDuty: incidents@legal-ai.pagerduty.com
```

**External**:
```
AWS Support: 1-866-321-2211 (Enterprise)
CloudFlare Support: 1-888-993-5273
Cyber Insurance: 1-800-XXX-XXXX
FBI Cyber: 1-800-CALL-FBI
```

### Appendix B: Tool Inventory

**Detection & Monitoring**:
- Prometheus/Grafana (metrics)
- ELK Stack (log aggregation)
- CloudWatch (AWS monitoring)
- Sentry (error tracking)

**Forensics**:
- Wireshark (network analysis)
- Volatility (memory forensics)
- Autopsy (disk forensics)
- tcpdump (packet capture)

**Response & Remediation**:
- Ansible (automation)
- kubectl (Kubernetes management)
- AWS CLI (cloud management)

### Appendix C: Useful Commands

**Investigation**:
```bash
# Check recent logins
last -n 50

# Find large file transfers
find /var/log/nginx -name "access.log*" -exec grep "POST\|GET" {} \; | awk '{print $10}' | sort -rn | head -20

# Check for unusual processes
ps aux --sort=-%cpu | head -20

# Network connections
netstat -tulpn | grep ESTABLISHED

# Check for rootkits
chkrootkit
rkhunter --check
```

**Log Analysis**:
```bash
# Failed login attempts
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn

# Successful logins
grep "Accepted password" /var/log/auth.log

# Database queries
tail -f /var/log/postgresql/postgresql-*.log | grep "ERROR\|FATAL"
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-15 | Security Team | Initial version |

**Review Schedule**:
- Quarterly review
- After major incidents
- When infrastructure changes
- When team changes

**Distribution**:
- All engineering team members
- IT operations
- Executive team
- Legal team

**Classification**: Internal - Confidential
**Retention**: 7 years

---

**This is a living document. Report any issues or suggestions to security@legal-ai.com**
