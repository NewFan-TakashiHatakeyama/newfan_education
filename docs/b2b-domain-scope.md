# B2B Redesign Scope Lock

## Source of Truth

- `プロダクト概要資料_改訂版_AI-DX人材育成B2B.md` (2026-05-25)
- `基本設計資料_改訂版_AI-DX人材育成B2B.md` (2026-05-25)
- `詳細設計資料_改訂版_AI-DX人材育成B2B.md` (2026-05-25)

These three revised documents define the education and B2B evidence domain.
The AI venture project domain (`/ventures`) is additionally governed by
[venture-governance-design.md](venture-governance-design.md). Its review findings,
implementation changes and verification evidence are tracked in
[venture-review-remediation.md](venture-review-remediation.md).
The venture ledgers are project evidence and decision indexes; they do not restore
the removed recruiting marketplace or execute production releases and payments.

## Removed Domains

- SNS / community timeline
- follow / follower
- public personal profile
- direct company matching
- opportunities and job marketplace
- direct DM / chat for recruiting
- application / proposal pipeline for matching
- contract / payment / team order management

## Retained and Expanded Domains

- company and tenant management
- user and learner management
- role template and roadmap assignment
- lesson and exercise execution
- submission and AI review
- mentor review approval hook
- evidence generation
- requirement and fit assessment
- sales summary report
- notification and audit log

## Route Policy

- marketing: `/`
- company: `/company/*`
- learner: `/learner/*`
- mentor: `/mentor/*`
- admin: `/admin/*`

Legacy B2C routes are redirected to the new B2B entry points for compatibility.

## Legacy Isolation Status

- API legacy domains are isolated behind disabled gate (`LEGACY_B2C_ENABLED = false`):
  - opportunities
  - messages/templates/threads
  - public-profile settings
  - portfolio artifacts
- Web legacy routes are redirected in `apps/web/next.config.ts`:
  - `/messages` -> `/company/reports`
  - `/portfolio/*` -> `/learner/evidence`
  - `/opportunities` and `/career` -> `/company/requirements`
