# Solidity Vulnerability Scanner — Pricing

## Tiers

| Tier                       | Price        | Includes                                                                                                                                                               |
| -------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Developer**              | Free         | 5 scans/month, HTML + SARIF reports, SWC mapping, community support                                                                                                    |
| **Team**                   | $299/month   | 100 scans/month, all report formats (HTML/SARIF/PDF/JSON), LLM audit enhancement, webhook integrations, email support                                                  |
| **Audit Firm API License** | $2,500/month | Unlimited scans, white-label API (`/api/v1/scan`), PDF professional audit reports with custom branding, priority queue, SLA (< 30s scan time), dedicated Slack channel |

## White-Label API Access (Audit Firm Tier)

Audit firms embed the scanner under their own brand:

```
POST /api/v1/scan
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "source_code": "pragma solidity ^0.8.0; ...",
  "report_format": "json",
  "branding": {
    "firm_name": "Your Audit Firm",
    "logo_url": "https://yourfirm.com/logo.png"
  }
}
```

Response includes: findings, SWC/CWE mapping, severity scores, remediation recommendations, SARIF for CI integration.

## GitHub Action (All Tiers)

```yaml
- uses: giselleevita/solidity-scan-action@v1
  with:
    api-key: ${{ secrets.SOLIDITY_SCANNER_KEY }}
    severity-gate: high # fail on HIGH or CRITICAL
    paths: contracts/
```

Free tier: 5 scans/month. Team+: included in quota.
