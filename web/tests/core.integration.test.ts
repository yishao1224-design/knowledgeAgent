import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { calculateStats, parseKnowledgePage } from "../lib/okf";
import { answerQuestion } from "../lib/answer";
import { createIngestPreview } from "../lib/ingest";
import { runQueryAgent } from "../lib/agent/query-agent";
import { runIngestAgent } from "../lib/agent/ingest-agent";
import { fixedRuntimeAssets } from "../lib/agent/fixed-runtime";
import { resolveAgentModel, testAgentModelConnection } from "../lib/agent/model";
import { normalizeRepositoryUrl, shallowCloneRepository } from "../lib/git-repository";
import type { LoadedRepository } from "../lib/git-repository";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const kbRoot = new URL("../../kb/", import.meta.url);

async function readMarkdownFiles(directory: URL, prefix = "kb"): Promise<Map<string, string>> {
  const files = new Map<string, string>();
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      const nested = await readMarkdownFiles(new URL(`${entry.name}/`, directory), `${prefix}/${entry.name}`);
      for (const item of nested) files.set(...item);
    } else if (entry.name.endsWith(".md")) {
      files.set(`${prefix}/${entry.name}`, await readFile(new URL(entry.name, directory), "utf8"));
    }
  }
  return files;
}

async function localRepository(): Promise<LoadedRepository> {
  const files = await readMarkdownFiles(kbRoot);
  const pages = [...files]
    .filter(([path]) => path !== "kb/index.md" && path !== "kb/log.md")
    .map(([path, text]) => parseKnowledgePage(path, text));
  return {
    repository: "https://github.com/yishao1224-design/knowledgeAgent",
    branch: "master",
    commit: "5973ecd000000000000000000000000000000000",
    clonedAt: new Date().toISOString(),
    pages,
    stats: calculateStats(pages),
    warnings: [],
    files,
  };
}

test("parses the repository and answers with citations", async () => {
  const repository = await localRepository();
  assert.equal(repository.stats.pages, 23);
  assert.equal(repository.stats.sources, 7);

  const answer = answerQuestion(
    repository.pages,
    "知识生命周期包括哪些状态？",
    repository.commit,
    repository.branch,
  );
  assert.ok(answer.citations.length > 0);
  assert.match(answer.answer, /知识生命周期|Knowledge Lifecycle/i);
  assert.match(answer.answer, /5973ecd/);
});

test("bundles hash-verified fixed skills and the original okf.py", () => {
  const runtime = fixedRuntimeAssets();
  const hash = (value: string) => createHash("sha256").update(value).digest("hex");
  assert.equal(runtime.manifest.runtimeVersion, "knowledge-agent-2026.08.15.1");
  assert.equal(hash(runtime.querySkill), runtime.manifest.files["skills/kb-query/SKILL.md"]);
  assert.equal(hash(runtime.ingestSkill), runtime.manifest.files["skills/kb-ingest/SKILL.md"]);
  assert.equal(hash(runtime.okfScript), runtime.manifest.files["scripts/okf.py"]);
  assert.match(runtime.okfScript, /def\s+cmd_lint|def\s+lint/);
});

test("normalizes supported public repository URLs", () => {
  assert.equal(
    normalizeRepositoryUrl("https://dev.azure.com/example-org/Knowledge Project/_git/okf-bundle?path=/kb"),
    "https://dev.azure.com/example-org/Knowledge%20Project/_git/okf-bundle",
  );
  assert.equal(
    normalizeRepositoryUrl("https://example-org@dev.azure.com/example-org/Knowledge%20Project/_git/okf-bundle"),
    "https://dev.azure.com/example-org/Knowledge%20Project/_git/okf-bundle",
  );
  assert.equal(
    normalizeRepositoryUrl("https://example-org.visualstudio.com/Knowledge%20Project/_git/okf-bundle/"),
    "https://example-org.visualstudio.com/Knowledge%20Project/_git/okf-bundle",
  );
  assert.throws(
    () => normalizeRepositoryUrl("https://dev.azure.com/example-org/Knowledge%20Project/okf-bundle"),
    /Azure DevOps 仓库地址/,
  );
});

test("requires repository username and password to be provided together", async () => {
  await assert.rejects(
    shallowCloneRepository("https://dev.azure.com/example-org/Knowledge%20Project/_git/okf-bundle", undefined, {
      username: "example-org",
    }),
    /仓库用户名和密码需要同时填写/,
  );
});

test("validates model configuration before running an agent", async () => {
  const longApiKey = `sk-${"a".repeat(900)}`;
  const config = resolveAgentModel({ apiKey: longApiKey, baseUrl: "https://api.example.com/v1", model: "example-model" });
  assert.equal(config.apiKey, longApiKey);
  assert.equal(config.baseUrl, "https://api.example.com/v1");

  const result = await testAgentModelConnection({ baseUrl: "https://api.example.com/v1", model: "example-model" });
  assert.equal(result.ok, false);
  assert.match(result.message, /API Key/);
});

test("lets Pi choose repository tools for a grounded query", async () => {
  const repository = await localRepository();
  const result = await runQueryAgent(
    {
      repository: repository.repository,
      branch: repository.branch,
      question: "What states are in the knowledge lifecycle?",
    },
    {
      cloneRepository: async () => repository,
      runAgent: async ({ tools }) => {
        await tools.find((tool) => tool.name === "load_skill")?.execute("skill-1", {});
        await tools.find((tool) => tool.name === "search_files")?.execute(
          "search-1",
          { query: "lifecycle", prefix: "concepts" },
        );
        await tools.find((tool) => tool.name === "read_file")?.execute(
          "read-1",
          { path: "kb/concepts/knowledge-lifecycle.md", startLine: 1, endLine: 120 },
        );
        return {
          answer: "The lifecycle is documented in [Knowledge Lifecycle](/concepts/knowledge-lifecycle.md).",
          model: "fake-pi-model",
        };
      },
    },
  );

  assert.ok(result.citations.length);
  assert.equal(result.workflow?.engine, "pi");
  assert.deepEqual(result.workflow?.steps.map((step) => step.node), [
    "shallow_clone",
    "load_skill",
    "search_files",
    "read_file",
  ]);
  assert.equal(result.workflow?.runtime?.skill, "kb-query");
});

test("creates a git-applicable ingest patch without changing old sources", async () => {
  const repository = await localRepository();
  const preview = await createIngestPreview(repository, {
    title: "Web Workspace Integration Preview",
    sourceUrl: "https://example.com/integration-preview",
    text: "This is a deterministic integration fixture used to verify that the patch-first ingest flow creates an immutable source, a draft concept, and updates the generated index and append-only log.",
  });

  assert.equal(preview.checks.passed, true, preview.checks.errors.join("\n"));
  assert.equal(preview.files.filter((file) => file.action === "create").length, 2);
  assert.doesNotMatch(preview.patch, /diff --git a\/kb\/sources\/2026-07/);

  const check = spawnSync("git", ["apply", "--check", "-"], {
    cwd: repoRoot,
    input: preview.patch,
    encoding: "utf8",
  });
  assert.equal(check.status, 0, check.stderr || check.stdout);
});

test("lets Pi inspect the bundle before drafting an ingest patch", async () => {
  const repository = await localRepository();
  const preview = await runIngestAgent(
    {
      repository: repository.repository,
      branch: repository.branch,
      material: {
        title: "Pi Agent Ingest Integration Preview",
        text: "This fixture confirms that Pi Agent autonomously inspects repository files before invoking the deterministic patch drafting and lifecycle validation tool.",
      },
    },
    {
      cloneRepository: async () => repository,
      runAgent: async ({ tools }) => {
        await tools.find((tool) => tool.name === "load_skill")?.execute("skill-1", {});
        await tools.find((tool) => tool.name === "read_file")?.execute(
          "read-schema",
          { path: "kb/SCHEMA.md", startLine: 1, endLine: 120 },
        );
        await tools.find((tool) => tool.name === "search_files")?.execute(
          "search-title",
          { query: "integration preview" },
        );
        await tools.find((tool) => tool.name === "draft_ingest")?.execute(
          "draft-1",
          { rationale: "No duplicate concept was found after inspecting the schema and bundle.", relatedPaths: ["kb/SCHEMA.md"] },
        );
        return { answer: "A reviewable patch was prepared.", model: "fake-pi-model" };
      },
    },
  );

  assert.equal(preview.checks.passed, true);
  assert.equal(preview.workflow?.engine, "pi");
  assert.deepEqual(preview.workflow?.steps.map((step) => step.node), [
    "shallow_clone",
    "load_skill",
    "read_file",
    "search_files",
    "draft_ingest",
  ]);
  assert.equal(preview.workflow?.runtime?.skill, "kb-ingest");
});
