# rana — UX Requirement Analysis Skill

[中文](./README.zh-CN.md) | English

A **agent skill** deployable to OpenClaw, OpenCode, Claude Code, and other CLI agent platforms. It helps UX designers turn PM PRDs into structured requirement analysis documents.

## What It Does

- **Quick Mode**: Fast 4-dimension analysis (Problem → Goal → Solution → Metrics) + clarifying questions
- **Full Mode**: 3-stage progressive analysis (Diagnosis → Solution → Refine) producing an 8-chapter deliverable
- **Built-in quality gate**: Automated `quality-validator.py` checks file structure, source traceability, P0 sections, chapter completeness, and vague terms

## Quick Start

```bash
# Install skill (adjust path for your agent platform)
cp -r rana/. ~/.agents/skills/rana/       # OpenCode / BlueCode
cp -r rana/. ~/.openclaw/skills/rana/     # OpenClaw

# Use in your agent session
# Just provide a PRD text, PDF, or screenshot — rana auto-detects input type
```

## Project Structure

```
rana/
├── SKILL.md                              # Skill entry — dual-mode routing + shared bootstrap
├── scripts/quality-validator.py          # CLI quality gate checker
├── references/
│   ├── workflow-quick-mode-guideline.md  # Quick Mode full workflow
│   ├── workflow-full-mode-guideline.md   # Full Mode full workflow
│   ├── collaboration-protocol.md         # Critique & collaboration rules (shared)
│   ├── p0-gates.md                       # P0 gap rules
│   ├── stage-1-diagnosis.md              # Diagnosis stage details
│   ├── stage-2-solution.md               # Solution stage details
│   ├── stage-3-refine.md                 # Refine stage details
│   ├── analysis-methods.md               # HMW / MVP / 5-Why / X-Y Problem
│   └── quality-validator.md              # Validator behavior docs
├── assets/
│   ├── analysis-template-full.md         # Full Mode output template (8 chapters)
│   └── analysis-template-quick.md        # Quick Mode output template
└── config.yaml                           # File parser config
```

## Testing

```bash
pip3 install pdfplumber ruff   # dev dependencies

python3 -m pytest tests/ -v    # run all tests (unit + e2e + integration)
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/e2e/ -v
python3 -m pytest tests/integration/ -v

ruff check rana/scripts/       # lint
```

## Development

1. Edit `rana/` source
2. Run `python3 -m pytest tests/ -v` — must stay green
3. Sync install copy: `cp -r rana/. ~/.agents/skills/rana/`

See [AGENTS.md](./AGENTS.md) for full development guidelines.

## License

Internal tool — not publicly distributed.