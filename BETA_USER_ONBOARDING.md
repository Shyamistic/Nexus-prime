# 🚀 Nexus Prime - Beta User Onboarding Guide

## Welcome to Nexus Prime Beta! 

Nexus Prime is an AI-powered autonomous incident response platform that revolutionizes how your team handles production incidents. This guide will get you up and running in minutes.

## 🎯 What You'll Get

### ✨ Core Features
- **AI-Powered Root Cause Analysis** - 90% accuracy in under 30 seconds
- **Multi-Platform Alert Ingestion** - Datadog, PagerDuty, Prometheus, and more
- **Real-Time Dashboard** - Live incident tracking with WebSocket updates
- **Automated Remediation** - One-click fixes for common issues
- **Smart Notifications** - Slack, Teams, Email, SMS with intelligent routing
- **Comprehensive Analytics** - MTTR tracking, resolution patterns, and more

### 🔥 Beta Program Benefits
- **Free Access** - Full platform access during beta period
- **Direct Support** - Priority support from our engineering team
- **Feature Influence** - Your feedback shapes our roadmap
- **Early Adopter Benefits** - Locked-in pricing when we launch

## 🚀 Quick Start (5 Minutes)

### Step 1: Create Your Account
1. Visit: `https://beta.nexus-prime.com/register`
2. Fill in your organization details:
   - **Organization Name**: Your company name
   - **Admin Email**: Your work email
   - **Admin Name**: Your full name
   - **Password**: Secure password (min 8 characters)
3. Click "Create Organization"

### Step 2: Get Your API Key
After registration, you'll receive:
- **Dashboard URL**: `https://beta.nexus-prime.com`
- **API Key**: For webhook integrations
- **Webhook URLs**: For your monitoring tools

### Step 3: Connect Your First Integration

#### Option A: Datadog Integration
```bash
# Add this webhook URL to your Datadog alerts:
https://api.nexus-prime.com/api/v1/ingest/webhook/datadog

# Headers:
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

#### Option B: PagerDuty Integration
```bash
# Add this webhook URL to your PagerDuty service:
https://api.nexus-prime.com/api/v1/ingest/webhook/pagerduty

# Headers:
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

#### Option C: Prometheus AlertManager
```yaml
# Add to your alertmanager.yml:
route:
  routes:
  - match:
      alertname: .*
    receiver: nexus-prime

receivers:
- name: nexus-prime
  webhook_configs:
  - url: 'https://api.nexus-prime.com/api/v1/ingest/webhook/prometheus'
    http_config:
      bearer_token: 'YOUR_API_KEY'
```

### Step 4: Configure Notifications
1. Go to **Settings** → **Notifications**
2. Add your team's communication channels:
   - **Slack**: Add webhook URL
   - **Microsoft Teams**: Add webhook URL
   - **Email**: Configure SMTP settings
   - **SMS**: Add phone numbers (Twilio integration)

### Step 5: Test Your Setup
1. Create a test incident using our API:
```bash
curl -X POST https://api.nexus-prime.com/api/v1/ingest/webhook/generic \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Incident - High CPU Usage",
    "summary": "CPU usage exceeded 90% on production server",
    "severity": "SEV2",
    "service_id": "web-server-01",
    "tags": ["cpu", "performance", "production"]
  }'
```

2. Watch the magic happen:
   - ✅ Incident appears in dashboard within seconds
   - 🤖 AI analysis completes in ~30 seconds
   - 📧 Notifications sent to your team
   - 🔧 Remediation steps suggested
   - 📊 Real-time updates via WebSocket

## 🎛️ Dashboard Overview

### Main Dashboard
- **Live Incidents**: Real-time incident feed
- **System Status**: Overall health indicators
- **Key Metrics**: MTTR, resolution rates, severity breakdown
- **Recent Activity**: Latest incidents and resolutions

### Incident Detail View
- **AI Analysis**: Root cause analysis with confidence score
- **Timeline**: Complete incident lifecycle
- **Remediation**: One-click automated fixes
- **Collaboration**: Team chat and notes
- **Analytics**: Impact assessment and patterns

### Settings & Configuration
- **Team Management**: Invite users, set roles
- **Integrations**: Connect monitoring tools
- **Notifications**: Configure alert channels
- **API Keys**: Manage webhook authentication

## 👥 Team Management

### User Roles
- **Admin**: Full access, user management, billing
- **SRE**: Incident management, remediation execution
- **Viewer**: Read-only access to incidents and analytics

### Inviting Team Members
1. Go to **Settings** → **Team**
2. Click **Invite User**
3. Enter email, name, and role
4. User receives invitation email
5. They create password and join your organization

## 🔧 Advanced Configuration

### Custom Webhook Integration
For tools not directly supported:
```bash
# Generic webhook endpoint:
POST https://api.nexus-prime.com/api/v1/ingest/webhook/generic

# Payload format:
{
  "title": "Incident Title",
  "summary": "Detailed description",
  "severity": "SEV1|SEV2|SEV3|SEV4",
  "source": "your-tool-name",
  "service_id": "affected-service",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "custom_field": "value"
  }
}
```

### API Authentication
All API calls require authentication:
```bash
# Header format:
Authorization: Bearer YOUR_API_KEY

# Or query parameter:
?api_key=YOUR_API_KEY
```

### Rate Limits
- **Webhook Ingestion**: 5,000 requests/hour per organization
- **API Calls**: 10,000 requests/hour per organization
- **Authentication**: 10 attempts/minute per IP

## 📊 Analytics & Reporting

### Key Metrics Tracked
- **MTTR (Mean Time to Resolution)**: Average incident resolution time
- **MTTA (Mean Time to Acknowledgment)**: Average response time
- **Incident Volume**: Trends and patterns
- **AI Accuracy**: Root cause analysis confidence
- **Resolution Patterns**: Common fixes and their effectiveness

### Custom Reports
- **Weekly Incident Summary**: Automated email reports
- **Monthly Analytics**: Detailed performance metrics
- **Trend Analysis**: Long-term patterns and improvements
- **Team Performance**: Individual and team statistics

## 🚨 Best Practices

### Incident Severity Guidelines
- **SEV1**: Complete service outage, revenue impact
- **SEV2**: Major functionality impaired, user impact
- **SEV3**: Minor issues, degraded performance
- **SEV4**: Informational, no immediate impact

### Effective Alert Configuration
1. **Avoid Alert Fatigue**: Set appropriate thresholds
2. **Use Tags Effectively**: Enable better categorization
3. **Include Context**: Rich metadata helps AI analysis
4. **Test Regularly**: Ensure integrations work correctly

### Team Workflow
1. **Acknowledge Quickly**: Respond to SEV1/SEV2 within 5 minutes
2. **Use AI Insights**: Review root cause analysis before investigating
3. **Execute Remediation**: Use one-click fixes when available
4. **Document Learnings**: Add notes for future reference
5. **Review Patterns**: Weekly analysis of incident trends

## 🆘 Support & Help

### Getting Help
- **In-App Chat**: Click the help icon in dashboard
- **Email Support**: beta-support@nexus-prime.com
- **Documentation**: https://docs.nexus-prime.com
- **Community Slack**: Join our beta user community

### Common Issues

#### Webhooks Not Working
1. Check API key is correct
2. Verify webhook URL is accessible
3. Check request format matches documentation
4. Review rate limits

#### AI Analysis Not Appearing
1. Ensure incident has sufficient context
2. Check AI service status in dashboard
3. Verify incident severity triggers analysis
4. Contact support if issue persists

#### Notifications Not Sending
1. Verify notification channels are configured
2. Check webhook URLs are valid
3. Test with simple incident first
4. Review notification rules and filters

## 🎯 Beta Program Goals

### What We're Testing
- **AI Accuracy**: Root cause analysis effectiveness
- **Performance**: Response times and scalability
- **Usability**: Dashboard and workflow efficiency
- **Integrations**: Compatibility with monitoring tools
- **Reliability**: System uptime and stability

### Your Feedback Matters
We want to hear about:
- **Feature Requests**: What's missing?
- **Usability Issues**: What's confusing?
- **Performance Problems**: What's slow?
- **Integration Challenges**: What doesn't work?
- **Success Stories**: What's working great?

### Feedback Channels
- **Weekly Check-ins**: Scheduled calls with product team
- **Feature Requests**: Submit via in-app feedback
- **Bug Reports**: Email beta-support@nexus-prime.com
- **Community Discussion**: Beta user Slack channel

## 🚀 Next Steps

### Week 1: Setup & Integration
- [ ] Complete account setup
- [ ] Connect first monitoring tool
- [ ] Configure notifications
- [ ] Invite team members
- [ ] Create test incident

### Week 2: Team Adoption
- [ ] Train team on dashboard
- [ ] Establish incident response workflow
- [ ] Configure additional integrations
- [ ] Set up custom alerts
- [ ] Review first week's incidents

### Week 3: Optimization
- [ ] Analyze AI accuracy and feedback
- [ ] Optimize alert thresholds
- [ ] Customize remediation actions
- [ ] Review team performance metrics
- [ ] Provide product feedback

### Ongoing: Mastery
- [ ] Weekly incident reviews
- [ ] Monthly analytics analysis
- [ ] Continuous workflow optimization
- [ ] Feature request submissions
- [ ] Community participation

## 📞 Contact Information

### Beta Program Team
- **Product Manager**: sarah@nexus-prime.com
- **Engineering Lead**: mike@nexus-prime.com
- **Customer Success**: jessica@nexus-prime.com

### Emergency Support
- **24/7 Support**: +1-555-NEXUS-1 (24/7)
- **Critical Issues**: critical@nexus-prime.com
- **Status Page**: https://status.nexus-prime.com

---

**Welcome to the future of incident management! 🚀**

We're excited to have you as a beta user and look forward to revolutionizing how your team handles incidents. Let's build something amazing together!