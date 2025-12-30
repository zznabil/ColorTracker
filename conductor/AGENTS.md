# AGENTS: CONDUCTOR

## OVERVIEW
Source of truth for project specs, workflows, and architectural history.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| **Product Specs** | `product.md` | Core functionality and product requirements. |
| **Guidelines** | `product-guidelines.md` | Visual and behavioral constraints. |
| **Workflows** | `workflow.md` | Development process and PR protocols. |
| **Tech Stack** | `tech-stack.md` | Tooling and dependency rationale. |
| **Roadmap** | `tracks.md` | Active feature tracks and milestones. |
| **Style Guides** | `code_styleguides/` | Python and General code standards. Includes **V3.4.2 Branchless Guard**. |
| **Archive** | `archive/` | Optimization records and historical specs. Contains **V3.4.2 Singularity Audit**. |

## CONVENTIONS
- **Spec-First**: Implementation must match `product.md` exactly. Update docs before code.
- **Archival Protocol**: Move performance sprint specs to `archive/` post-merge.
- **Diagram Persistence**: All data flows must use Mermaid.js in docs.

## ANTI-PATTERNS
- **Ghost Specs**: Implementing features not documented in `product.md`.
- **Stale Tracks**: Leaving completed items in `tracks.md` (prune to archive).
- **Implicit Knowledge**: Relying on PR comments for logic; move to `conductor/` docs.
