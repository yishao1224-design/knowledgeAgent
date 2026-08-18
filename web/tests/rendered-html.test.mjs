import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the knowledge workspace", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Knowledge Workspace/);
  assert.match(html, /Open an OKF repository/);
  assert.match(html, /fresh, depth-one clone/i);
  assert.match(html, /No database/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Your site is taking shape/i);
});

test("exposes the fixed runtime manifest without exposing asset contents", async () => {
  const response = await render("/api/runtime");
  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.runtimeVersion, "knowledge-agent-2026.08.15.1");
  assert.equal(payload.sourceCommit, "5973ecd922e27ac66cd42215e025d829db2adc4e");
  assert.equal(payload.pythonProcessAvailable, false);
  assert.equal(payload.okfExecution, "typescript-adapter");
  assert.match(payload.files["scripts/okf.py"], /^[a-f0-9]{64}$/);
  assert.equal("okfScript" in payload, false);
});

test("Pi Agent autonomously uses repository tools around a depth-one clone", async () => {
  const source = await readFile(new URL("../lib/git-repository.ts", import.meta.url), "utf8");
  const repositoryRoute = await readFile(new URL("../app/api/repository/route.ts", import.meta.url), "utf8");
  const askRoute = await readFile(new URL("../app/api/ask/route.ts", import.meta.url), "utf8");
  const ingestRoute = await readFile(new URL("../app/api/ingest/route.ts", import.meta.url), "utf8");
  const queryAgent = await readFile(new URL("../lib/agent/query-agent.ts", import.meta.url), "utf8");
  const ingestAgent = await readFile(new URL("../lib/agent/ingest-agent.ts", import.meta.url), "utf8");
  const runtime = await readFile(new URL("../lib/agent/runtime.ts", import.meta.url), "utf8");
  const fixedRuntime = await readFile(new URL("../lib/agent/fixed-runtime.ts", import.meta.url), "utf8");

  assert.match(source, /depth:\s*1/);
  assert.match(source, /singleBranch:\s*true/);
  assert.match(source, /noTags:\s*true/);
  assert.match(repositoryRoute, /shallowCloneRepository/);
  assert.match(askRoute, /runQueryAgent/);
  assert.match(ingestRoute, /runIngestAgent/);
  assert.match(queryAgent, /createReadOnlyRepositoryTools/);
  assert.match(queryAgent, /"shallow_clone"/);
  assert.match(ingestAgent, /"draft_ingest"/);
  assert.match(runtime, /new Agent/);
  assert.match(runtime, /MAX_TOOL_CALLS/);
  assert.match(fixedRuntime, /load_skill/);
  assert.match(fixedRuntime, /FIXED_OKF_SCRIPT/);
});
