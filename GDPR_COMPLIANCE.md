# GDPR Compliance Package — Tripo3D MVP (ASCENTIA s.r.o.)

## 1. Data Flow Map

```
User Photo (JPG/PNG/WebP)
    │
    ▼
┌─────────────────────────────────────────────┐
│  ASCENTIA s.r.o. (Controller)               │
│  IČO: 51858959, Bratislava, SK              │
│  Hosting: Render (Ohio, USA)                │
│  Code: https://github.com/Abra7abra7/tripo-mvp │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────────┐  ┌──────────────┐
│ Render (US)  │  │ Tripo (US)   │
│ Hosting / FS │  │ AI 3D Gen    │
│ DPA: ✅      │  │ DPA: ⚠️      │
│ EU-US DPF ✅ │  │ Sec 7 ToS    │
└──────────────┘  └──────────────┘
```

## 2. Processor Status

| Processor | Role | Location | DPA | Data Access | Notes |
|-----------|------|----------|-----|-------------|-------|
| **Render Inc.** | Subprocessor (hosting) | Ohio, USA | ✅ Available on request | Full disk access | EU-US DPF certified, SOC 2, ISO 27001 |
| **Tripo / Holymolly Ltd** | Subprocessor (AI API) | USA | ⚠️ Not explicitly offered | Photo sent via API | ToS Sec 7 covers security; Sec 5.2.2 paid users own outputs |

## 3. Action Items Checklist

### 🔴 High Priority (do before selling)

- [x] **Request DPA from Render** — ✅ email sent to security@render.com (Aug 4, 2026)
- [x] **Request DPA from Tripo** — ✅ email sent to support@tripo3d.ai (Aug 4, 2026)
- [ ] **Upgrade Render to paid plan (Frankfurt, EU)** — free tier is Ohio (US data transfer). ⚠️ Render API potvrdila: free plan podporuje LEN Ohio. Pre Frankfurt treba upgradnut na starter ($7/mes) cez dashboard
- [x] **Add Privacy Policy** — ✅ Done at /privacy
- [x] **Add data retention (30d auto-delete)** — ✅ Done (startup cleanup)
- [ ] **Update Terms of Service link** on website

### 🟡 Medium Priority

- [ ] **Register data processing activities** — internal record under Art. 30 GDPR
- [ ] **Add cookie-free banner / notice** — not needed (no cookies), but document it
- [ ] **Create internal Data Retention Policy** document
- [ ] **Set up deletion request process** — email to ascentia@agentmail.to works

### 🟢 Low Priority (for scaling)

- [ ] **EU-US Data Privacy Framework verification** — check Tripo's certification status
- [ ] **SCCs (Standard Contractual Clauses)** — if Tripo doesn't certify under DPF
- [ ] **Appoint DPO** (not required for <250 employees unless large-scale processing)
- [ ] **DPIA (Data Protection Impact Assessment)** — not required for photo-to-3D unless processing special categories

## 4. GDPR Articles Mapping

| GDPR Article | Requirement | Status |
|---|---|---|
| Art. 5 | Lawfulness, fairness, transparency | ✅ Privacy Policy published |
| Art. 6(1)(b) | Processing necessary for contract performance | ✅ Legal basis established |
| Art. 12-14 | Information to data subject | ✅ Privacy Policy |
| Art. 15 | Right of access | ✅ Contact email |
| Art. 17 | Right to erasure | ✅ Auto-delete + manual request |
| Art. 28 | Data Processing Agreement | ⚠️ Render: request; Tripo: request |
| Art. 30 | Records of processing activities | ⚠️ Create internal document |
| Art. 32 | Security of processing | ✅ HTTPS, auth, file cleanup |
| Art. 44-49 | International transfers | ⚠️ US transfers via DPF/SCCs |

## 5. Legal Basis by Data Type

| Data Type | Legal Basis | GDPR Article |
|-----------|------------|--------------|
| Uploaded photo | Contract performance (service provision) | Art. 6(1)(b) |
| Generated 3D models | Contract performance | Art. 6(1)(b) |
| IP address / logs | Legitimate interest (security, operations) | Art. 6(1)(f) |

## 6. Tripo Terms — Key Clauses for Compliance

Source: https://www.tripo3d.ai/terms (last updated July 11, 2025)

- **Section 3.4 (Third Party Services):** Tripo disclaims responsibility for third-party services including their own API
- **Section 5.2.2 (Paid Users):** Paid users retain full IP rights to Inputs and Outputs. Company will NOT use inputs/outputs as training data
- **Section 7 (Security):** Holymolly maintains security program incl. MFA, encryption, incident response
- **Section 6.1 (Payment):** Via Stripe — no payment data stored by Tripo or ASCENTIA
- **Section 11 (Governing Law):** Check for applicable jurisdiction

## 7. Render Security — Key Facts

Source: https://render.com/security

- **SOC 2 Type 2** certified
- **ISO 27001** certified
- **GDPR-DPA** available on request
- **EU-US Data Privacy Framework** certified (including UK extension)
- **Subprocessors:** AWS (US), GCP (US), Cloudflare (US), ClickHouse (US)
- **Shared Responsibility Model** documented

## 8. Recommended Privacy Policy Text for T&C

Include in your Terms of Service:

> **Data Processing.** By using the Service, you acknowledge that your uploaded images are transmitted to Tripo AI (Holymolly Ltd) for 3D model generation. ASCENTIA s.r.o. acts as data controller and has engaged Render Inc. as data processor. Both entities are certified under the EU-US Data Privacy Framework. Uploaded images and generated models are retained for a maximum of 30 days and automatically deleted thereafter. You may request earlier deletion by contacting ascentia@agentmail.to.

---

*Document prepared: August 4, 2026*
*This document is for informational purposes and does not constitute legal advice. Consult with a qualified attorney for full GDPR compliance.*