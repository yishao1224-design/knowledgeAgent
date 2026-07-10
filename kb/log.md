# Bundle Update Log

## 2026-07-10
* **Update**: added *Source assets* convention to [SCHEMA.md](/SCHEMA.md) — keep load-bearing visuals (dense architecture diagrams) as immutable files under sources/assets/, re-read on ingest and review; kb-ingest and kb-review skills gained the matching steps.

## 2026-07-09
* **Ingestion**: ado-workitem-sync toolchain from [capture](/sources/2026-07-09-ado-workitem-sync.md); created [ado-workitem-sync entity](/entities/ado-workitem-sync.md), linked from [ingesting-requirements](/concepts/ingesting-requirements-from-ticket-systems.md).
* **Update**: refined access paths in [ingesting-requirements](/concepts/ingesting-requirements-from-ticket-systems.md) from first field use — pick by judgment-vs-mechanical shape (MCP interactive, script+REST for pipelines), added rev-stamp provenance rule for mutable retrieval caches.
* **Update**: added one-project-multiple-repos hybrid to [adopting-the-bundle-pattern](/concepts/adopting-the-bundle-pattern.md) — sibling standalone KB repo, process-link DoD, workspace/CLAUDE.md convention, tag-scoping by module, integration-contract guidance.

## 2026-07-08
* **Ingestion**: filed session takeaways on trust semantics — page-as-unit-of-trust, weakest-link rules, needs_review as detector convergence point added to [knowledge-lifecycle](/concepts/knowledge-lifecycle.md); multi-story ingest discipline (no re-warranting, evolution vs contradiction) added to [user-story-analysis-workflow](/concepts/user-story-analysis-workflow.md).
* **Update**: added analysis-time code cross-check to [user-story-analysis-workflow](/concepts/user-story-analysis-workflow.md) — trust-label updates during story analysis with scope/asymmetric-authority/three-way-mismatch guardrails.
* **Ingestion**: filed conversation takeaways on the ingest-after-verify story pipeline; created [user-story-analysis-workflow](/concepts/user-story-analysis-workflow.md), linked from [ingesting-requirements](/concepts/ingesting-requirements-from-ticket-systems.md).
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