# cdc

## Overview
The **cdc** project is a clock-domain-crossing (CDC) analysis toolkit that aims to make sign-off quality CDC verification accessible to small and large hardware teams alike. The tool parses HDL sources, builds an annotated connectivity graph, and applies a library of structural and protocol-level checks to flag unsafe domain crossings before they escape to silicon. The long-term vision is to provide both a scriptable engine for automated regressions and ergonomic reporting for design and verification engineers.

## Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/cdc.git
   cd cdc
   ```
2. **Create an isolated Python environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install the package in editable mode** so that local changes are immediately available to the CLI.
   ```bash
   pip install -e .
   ```
   > A `pyproject.toml` and dependency lock file will be published as the core modules solidify. Until then, install any additional optional dependencies (for waveform parsing or vendor-specific format support) manually as needed.

## Usage
Once installed, the `cdc` CLI becomes available. The following snippets illustrate typical workflows:

```bash
# Run a full CDC analysis across a design database
cdc analyze --top chip_top --hdl rtl/**/*.sv --constraints constraints/cdc.sdc

# Generate a summary report focused on synchronizer coverage
cdc report --input results/chip_top.cdcdb --format markdown --output reports/sync-summary.md

# Diff two analysis runs to understand the impact of RTL changes
cdc diff --baseline results/chip_top.prev.cdcdb --revised results/chip_top.new.cdcdb
```

All commands accept `--help` for additional options, including incremental analysis modes and integration with third-party linting pipelines.

## Supported CDC Rules
The analyzer currently focuses on the high-value rule families below. Each rule can be enabled or disabled through the command-line interface or YAML configuration files:

- **Missing synchronizer detection** – Flags crossings without the expected two-flop (or custom) synchronizer structures.
- **Combinational fan-out crossings** – Identifies unsynchronized combinational logic feeding asynchronous domains.
- **Glitch-prone reconvergence** – Detects divergent synchronized paths that reconverge in logic susceptible to glitches.
- **Handshake protocol validation** – Checks that request/acknowledge interfaces obey multi-cycle sequencing guarantees.
- **Reset domain alignment** – Verifies that asynchronous resets are synchronized before use in a new clock domain.
- **Clock ratio assumptions** – Ensures constraints about fast-to-slow or slow-to-fast domain crossings are honored.

Upcoming rules (see Roadmap) will expand coverage to FIFO depth reasoning and multi-bit CDC protocol verification.

## Internal Architecture
The repository is organized to keep the analysis engine modular and extensible:

- `cdc/parser/`
  - Responsible for ingesting HDL sources (SystemVerilog, VHDL, and gate-level netlists) and constructing an intermediate representation (IR).
  - Extension points: add new `Frontend` subclasses for proprietary netlist formats or simulation dumps.
- `cdc/analyzer/`
  - Hosts the core dataflow graph, clock-domain propagation logic, and the rule evaluation engine.
  - Extension points: implement new rule classes derived from `BaseRule` with access to the IR and clock graph APIs.
- `cdc/reports/`
  - Contains report generators that serialize analysis results to Markdown, HTML, JSON, or custom dashboards.
  - Extension points: create new `ReportBackend` implementations or customize templating for enterprise reporting.
- `cdc/cli/`
  - Wraps Click-based commands that orchestrate parsing, analysis, and reporting from the terminal.
  - Extension points: register new subcommands for bespoke workflows (e.g., regression dashboards or ECO validation).
- `cdc/integrations/`
  - Houses adapters for EDA toolchains (e.g., Synopsys Verdi, Cadence JasperGold) and CI services.
  - Extension points: contribute additional exporters or ingestion hooks for vendor-specific databases.
- `tests/`
  - Organizes unit tests by module, along with reusable HDL fixtures for exercising specific CDC scenarios.

Design contributors should orient themselves with the module-level README files (to be added) for deeper guidance on APIs, type expectations, and service contracts.

## Contribution Guidelines
We welcome contributions that improve CDC coverage, usability, and ecosystem integrations. Please follow the practices below to keep the project healthy:

- **Coding style** – Python code must conform to [PEP 8](https://peps.python.org/pep-0008/). Format patches with `black` (line length 100) and sort imports with `isort` before submitting. Static checks via `ruff` are run in CI.
- **Type checking** – Run `mypy` targeting Python 3.10 to ensure type annotations remain accurate across modules.
- **Testing** – Add or update tests under `tests/` for all logic changes. Execute `pytest` locally and ensure new HDL fixtures are minimal yet illustrative.
- **Documentation** – Update this README or module-level docs when extending the CLI, adding rules, or modifying configuration schemas.
- **Commit hygiene** – Write descriptive commit messages and avoid force-pushing to shared branches. Discuss large architectural changes via issues before opening a PR.

Planned user experience enhancements include a lightweight web dashboard for interactive triage and integrations with GitHub Actions, GitLab CI, and in-house Jenkins pipelines to automate CDC checks in pull requests.

## Roadmap
- ✅ Finalize the intermediate representation (IR) and rule plug-in API.
- 🔄 Expand parser coverage to mixed-language projects and vendor-specific netlist dumps.
- 🔄 Deliver HTML and JSON report exporters, including hyperlinks to waveform evidence.
- 🔄 Ship a beta web-based GUI for reviewing CDC violations collaboratively.
- 🔄 Publish container images for cloud-based regression farms and CI/CD integrations.
- 🛠️ Investigate automatic waiver management synchronized with requirements tracking systems.

Contributions that align with the roadmap—or propose new strategic directions—are highly encouraged. Feel free to open an issue to discuss ideas before implementation.
