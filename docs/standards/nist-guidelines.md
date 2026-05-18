# NIST Guidelines — Risk Framework Foundations

Summaries of the NIST publications that inform this project's risk-scoring
framework. Each section gives a general overview, then notes how it maps to
defending MCP servers from agent threats.

## At a Glance

| Document | Purpose | MCP Connection |
|----------|---------|----------------|
| FIPS 199 | Categorize information/systems by impact (CIA × Low/Mod/High) | Defines impact tiers for MCP tools |
| SP 800-60 | Map information types to FIPS 199 categories | Data dictionary for static scoring |
| SP 800-30 | Conduct risk assessments | Core methodology for the scoring engine |
| SP 800-83 | Malware incident prevention and handling | Response model for compromised agents |

## FIPS 199 — Security Categorization

**Standards for Security Categorization of Federal Information and Information
Systems.**

### General

Every system is rated against three security objectives and three impact
levels.

Objectives (CIA):

- **Confidentiality** — preventing unauthorized disclosure
- **Integrity** — preventing unauthorized modification
- **Availability** — ensuring timely, reliable access

Impact levels:

- **Low** — limited adverse effect
- **Moderate** — serious adverse effect
- **High** — severe or catastrophic adverse effect

The security category of a system is:

```
SC = {(confidentiality, impact), (integrity, impact), (availability, impact)}
```

Overall categorization follows the **high-water mark**: the system inherits
the highest impact level assigned to any one objective.

### MCP Application

Each MCP tool exposes a CIA triple. Examples:

- `file_read` on `/etc/passwd` → (High, Low, Low) — confidentiality dominates
- `db_execute DELETE` → (Low, High, High) — integrity + availability
- `email_send` to external recipient → (High, Low, Low) — exfiltration risk

FIPS 199 levels become a categorical input to the **static** risk score —
what could a tool damage if misused, independent of who calls it?

## SP 800-60 — Mapping Information Types to Categories

**Guide for Mapping Types of Information and Information Systems to Security
Categories.**

### General

Two volumes:

- **Vol 1** — methodology for mapping information types to FIPS 199 impacts
- **Vol 2** — catalog of common information types with provisional ratings

Process:

1. Identify the information types the system handles
2. Assign provisional impact (from Vol 2 catalog)
3. Adjust for mission context, criticality, regulatory requirements
4. Aggregate to a system-wide category (high-water mark, per FIPS 199)

### MCP Application

Build an MCP-specific catalog — not of document types, but of tool surfaces:

- **Input types**: paths, SQL queries, shell args, identifiers
- **Output types**: records, file contents, command results
- **Side-effect targets**: filesystems, databases, network endpoints, processes

Each surface type gets a provisional impact rating. A tool's static score is
derived from the highest-rated surface it touches. This is the data dictionary
the framework consults at design time.

## SP 800-30 — Risk Assessment Methodology

**Guide for Conducting Risk Assessments.**

### General

NIST's risk model:

```
Risk = f(Threat Source, Threat Event, Vulnerability, Impact, Likelihood)
```

Components:

- **Threat source** — actor or condition that initiates events
- **Threat event** — action that exploits a vulnerability
- **Vulnerability** — weakness that can be exploited
- **Adverse impact** — what is lost when the event succeeds
- **Likelihood** — probability the event occurs

Process: **prepare → conduct → communicate → maintain**.

### MCP Application

This is the most direct fit for the project — the framework *is* a continuous,
automated risk assessment for MCP tool invocations.

| 800-30 Concept | MCP Mapping |
|----------------|-------------|
| Threat source | The AI agent (or the user behind it) |
| Threat event | A specific tool call |
| Vulnerability | Tool permissions, missing guards, broad scopes |
| Impact | FIPS 199 categorization of the tool's surface |
| Likelihood | Dynamic factors — input patterns, call frequency, context reuse |

- **Static** scoring ≈ pre-computed vulnerability × impact
- **Dynamic** scoring ≈ runtime likelihood × impact adjustments

## SP 800-83 — Malware Incident Handling

**Guide to Malware Incident Prevention and Handling for Desktops and Laptops.**

> If you meant **SP 800-53** (Security and Privacy Controls) instead, that
> publication catalogs the access-control, audit, and monitoring controls a
> defender deploys — often a closer fit for designing the *enforcement* side
> of this framework. Both are noted below.

### General (800-83)

Endpoint-focused malware lifecycle, in four phases:

1. **Preparation** — policies, tooling, training
2. **Detection & analysis** — identify and scope incidents
3. **Containment, eradication, recovery** — limit spread, remove threat, restore
4. **Post-incident** — lessons learned, update controls

### MCP Application

A jailbroken or compromised agent behaves like malware on the wire:
unauthorized calls, data exfiltration, privilege escalation. The four-phase
model maps to what happens *after* the risk score flags a request:

- **Preparation** — pre-defined deny/throttle policies tied to score thresholds
- **Detection** — the scoring engine itself
- **Containment** — refuse the call, revoke the session, isolate the agent
- **Post-incident** — log the event, refine static scores, update the threat
  model

## How They Fit Together

```
FIPS 199          → defines what "impact" means (CIA × L/M/H)
   │
   ▼
SP 800-60         → assigns impact to specific information / tool types
   │
   ▼
SP 800-30         → combines impact with threat + likelihood = risk
   │
   ▼
SP 800-83 / 53    → what to do when measured risk is too high
```

For the framework:

- **Static score inputs** come from FIPS 199 + SP 800-60 — what does this tool
  put at risk?
- **Scoring engine** follows SP 800-30 — how do we combine the factors?
- **Enforcement** borrows from SP 800-83 / 800-53 — gate, throttle, deny, log

## References

NIST publications can be retrieved from the NIST Computer Security Resource
Center publications hub:

- FIPS 199 — *Standards for Security Categorization of Federal Information and
  Information Systems*
- NIST SP 800-60 Vol. 1 / Vol. 2 Rev. 1 — *Guide for Mapping Types of
  Information and Information Systems to Security Categories*
- NIST SP 800-30 Rev. 1 — *Guide for Conducting Risk Assessments*
- NIST SP 800-83 Rev. 1 — *Guide to Malware Incident Prevention and Handling
  for Desktops and Laptops*
- NIST SP 800-53 Rev. 5 — *Security and Privacy Controls for Information
  Systems and Organizations* (related; relevant if the enforcement layer is
  in scope)
