# Bundle Update Log

## 2026-07-08
* **Update**: added okf.py `links` subcommand — expands `[[slug]]` authoring shorthand into canonical bundle-relative links (resolve by stem/title/path, skip code spans, leave ambiguous/missing in place); lint now flags surviving wiki-links. Revised [SCHEMA.md](/SCHEMA.md) link rule (sugar allowed, expand before index/lint) and [okf-toolchain](/entities/okf-toolchain.md) (seven subcommands).
* **Update**: added *Keeping code knowledge fresh* to [ingesting-requirements](/concepts/ingesting-requirements-from-ticket-systems.md) — story Definition-of-Done as primary code-knowledge freshness trigger, review_after as backstop; reconciled its review-cadence note with the scoped [SCHEMA.md](/SCHEMA.md) rule.
* **Update**: reworked [SCHEMA.md](/SCHEMA.md) review cadence — review_after is now an explicitly-scoped backstop (change-signal vs no-signal), internal maintainer field; story-driven pages defer to the DoD trigger per [ingesting-requirements](/concepts/ingesting-requirements-from-ticket-systems.md).

## 2026-07-07
* **Ingestion**: okf.py toolchain from [capture](/sources/2026-07-07-okf-toolchain.md); created [okf-toolchain entity](/entities/okf-toolchain.md), linked from [lifecycle-skills](/entities/lifecycle-skills.md).
* **Ingestion**: lifecycle skills from [capture](/sources/2026-07-06-lifecycle-skills.md); created [lifecycle-skills entity](/entities/lifecycle-skills.md), linked from [knowledge-lifecycle](/concepts/knowledge-lifecycle.md).

## 2026-07-06
* **Update**: added domain-concept body template to [SCHEMA.md](/SCHEMA.md) (required/optional sections, no N/A placeholders, artifact-reference rules); kb-ingest skill now points to it.
* **Ingestion**: filed conversation analyses on lifecycle automation and team merge guardrails; created [automating-the-lifecycle](/concepts/automating-the-lifecycle.md) and [pr-quality-gates](/concepts/pr-quality-gates.md), linked from [adopting-the-bundle-pattern](/concepts/adopting-the-bundle-pattern.md).
* **Ingestion**: filed conversation analysis on ingesting Azure DevOps user stories; created [ingesting-requirements-from-ticket-systems](/concepts/ingesting-requirements-from-ticket-systems.md), updated [adopting-the-bundle-pattern](/concepts/adopting-the-bundle-pattern.md) with populating-after-bootstrap section.
* **Ingestion**: filed conversation analysis on adopting the bundle pattern in project repos; created [adopting-the-bundle-pattern](/concepts/adopting-the-bundle-pattern.md), cross-linked from [knowledge-lifecycle](/concepts/knowledge-lifecycle.md).
* **Ingestion**: codebase-memory-mcp analysis from [source](/sources/2026-07-06-codebase-memory-mcp.md); created [entity](/entities/codebase-memory-mcp.md) and [comparison](/comparisons/codebase-memory-mcp-vs-kb-wiki.md).

## 2026-07-05
* **Creation**: seeded bundle with [OKF](/concepts/open-knowledge-format.md) and [lifecycle](/concepts/knowledge-lifecycle.md) concepts from [spec capture](/sources/2026-07-05-okf-spec-v0-1.md).
* **Initialization**: Bundle structure created — [SCHEMA.md](/SCHEMA.md), directory skeleton, toolchain, and lifecycle skills.