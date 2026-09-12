# Application visual theme

The signed-in application shares the landing page's teal, navy, warm white and cream palette. Brand tokens live in `apps/web/app/globals.css`; application CSS modules and inline styles consume these tokens.

| Token | Color | Usage |
| --- | --- | --- |
| `--primary` | `#116e63` | Primary actions, progress, active controls |
| `--primary-strong` | `#0c554c` | Hover actions and links |
| `--text` | `#17323b` | Text and navigation background |
| `--text-muted` | `#52656c` | Supporting text |
| `--bg` | `#f4f7f3` | Page canvas |
| `--surface-muted` | `#edf2ee` | Secondary surfaces |
| `--border` | `#dce5e1` | Card and section separators |

White text on primary teal has approximately 6:1 contrast. The navy sidebar locally overrides supporting text and focus colors for contrast. Active navigation also uses an inset marker. Errors remain red, warnings amber, and completion indicators green, with their existing labels.

Use white cards, restrained borders and 8–12px control/card corners. Cream highlights distinguish KPI cards. Dialog headers and action areas use the page canvas color; text inputs fill their panel. Below 960px the header wraps and the sidebar toggle hides the navigation when collapsed. Focus indicators and reduced-motion behavior remain enabled.

Validation: lint, web tests, production build; browser checks of dashboard, requirements drawer, learner home and venture navigation at desktop and mobile widths. CI additionally runs API and PostgreSQL/E2E checks before release.
