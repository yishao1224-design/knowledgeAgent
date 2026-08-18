import { createTwoFilesPatch } from "diff";
import { generateIndex, parseKnowledgePage, updateLog, validateBundle } from "./okf";
import type { IngestPreview, KnowledgePage } from "./types";
import type { LoadedRepository } from "./git-repository";

export interface IngestInput {
  title: string;
  text: string;
  sourceUrl?: string;
}

export function validateIngestInput(input: IngestInput): { title: string; text: string } {
  const title = input.title.trim();
  const text = input.text.trim();
  if (title.length < 2) throw new Error("请填写资料标题。");
  if (title.length > 180) throw new Error("资料标题不能超过 180 个字符。");
  if (text.length < 40) throw new Error("资料内容至少需要 40 个字符。");
  if (text.length > 200_000) throw new Error("单次 Ingest 内容不能超过 200,000 个字符。");
  return { title, text };
}

function slugify(value: string): string {
  const slug = value
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
  return slug || `note-${Date.now().toString(36)}`;
}

function quoteYaml(value: string): string {
  return JSON.stringify(value.replace(/\s+/g, " ").trim());
}

function conciseDescription(text: string): string {
  const clean = text.replace(/^#{1,6}\s+/gm, "").replace(/\s+/g, " ").trim();
  return clean.slice(0, 150) || "Knowledge captured through the web workspace.";
}

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function newFilePatch(path: string, content: string): string {
  const normalized = content.replace(/\n$/, "");
  const lines = normalized ? normalized.split("\n") : [];
  return [
    `diff --git a/${path} b/${path}`,
    "new file mode 100644",
    "--- /dev/null",
    `+++ b/${path}`,
    `@@ -0,0 +1,${lines.length} @@`,
    ...lines.map((line) => `+${line}`),
    "",
  ].join("\n");
}

function changedFilePatch(path: string, before: string, after: string): string {
  return `diff --git a/${path} b/${path}\n${createTwoFilesPatch(
    `a/${path}`,
    `b/${path}`,
    before,
    after,
    "before",
    "after",
    { context: 3 },
  )}`;
}

export async function createIngestPreview(
  repository: LoadedRepository,
  input: IngestInput,
): Promise<IngestPreview> {
  const { title, text } = validateIngestInput(input);

  const date = new Date().toISOString().slice(0, 10);
  let slug = slugify(title);
  let suffix = 1;
  while (repository.files.has(`kb/sources/${date}-${slug}.md`) || repository.files.has(`kb/concepts/${slug}.md`)) {
    suffix += 1;
    slug = `${slugify(title)}-${suffix}`;
  }

  const sourcePath = `kb/sources/${date}-${slug}.md`;
  const conceptPath = `kb/concepts/${slug}.md`;
  const sourceBody = `# ${title}\n\n${text}\n`;
  const hash = await sha256(sourceBody);
  const source = [
    "---",
    "type: Source",
    `title: ${quoteYaml(title)}`,
    `description: ${quoteYaml(`Verbatim capture submitted through the web workspace: ${conciseDescription(text)}`)}`,
    ...(input.sourceUrl?.trim() ? [`source_url: ${quoteYaml(input.sourceUrl.trim())}`] : []),
    `ingested: ${date}`,
    `sha256: ${hash}`,
    "---",
    "",
    sourceBody.trimEnd(),
    "",
  ].join("\n");

  const schema = repository.files.get("kb/SCHEMA.md") || "";
  const hasUnverifiedTag = schema.includes("`unverified`");
  const concept = [
    "---",
    "type: Concept",
    `title: ${quoteYaml(title)}`,
    `description: ${quoteYaml(conciseDescription(text))}`,
    "status: draft",
    "confidence: low",
    `created: ${date}`,
    `updated: ${date}`,
    ...(hasUnverifiedTag ? ["tags: [unverified]"] : []),
    "sources:",
    `  - /sources/${date}-${slug}.md`,
    "---",
    "",
    `# ${title}`,
    "",
    "## Definition",
    "",
    conciseDescription(text),
    "",
    "## Key Behaviors",
    "",
    "- This page is a draft created from a newly captured source and requires review before promotion.",
    "",
    "## Related Concepts",
    "",
    "- [Bundle Schema & Conventions](/SCHEMA.md) defines the lifecycle and content rules applied to this draft.",
    "",
    "# Citations",
    "",
    `1. [${title}](/sources/${date}-${slug}.md) — captured source.`,
    "",
  ].join("\n");

  const newPages: KnowledgePage[] = [
    ...repository.pages,
    parseKnowledgePage(sourcePath, source),
    parseKnowledgePage(conceptPath, concept),
  ];
  const indexBefore = repository.files.get("kb/index.md") || "";
  const logBefore = repository.files.get("kb/log.md") || "# Bundle Update Log\n";
  const indexAfter = generateIndex(newPages);
  const sourceBundlePath = `/sources/${date}-${slug}.md`;
  const conceptBundlePath = `/concepts/${slug}.md`;
  const logAfter = updateLog(
    logBefore,
    `**Ingestion**: ${title} from [capture](${sourceBundlePath}); created [draft concept](${conceptBundlePath}).`,
    date,
  );
  const checks = validateBundle(newPages);

  const patch = [
    newFilePatch(sourcePath, source),
    newFilePatch(conceptPath, concept),
    changedFilePatch("kb/index.md", indexBefore, indexAfter),
    changedFilePatch("kb/log.md", logBefore, logAfter),
  ].join("\n");

  return {
    commit: repository.commit,
    branch: repository.branch,
    plan: [
      `将提交内容保存为不可变 source capture：${sourceBundlePath}`,
      `创建低置信度 draft 概念页：${conceptBundlePath}`,
      "重新生成 kb/index.md，并追加 kb/log.md 记录",
      "不修改任何已有 kb/sources 文件；下载 Patch 后由本地 okf.py 做最终 lint",
    ],
    files: [
      { path: sourcePath, action: "create" },
      { path: conceptPath, action: "create" },
      { path: "kb/index.md", action: "update" },
      { path: "kb/log.md", action: "update" },
    ],
    patch,
    checks: {
      passed: checks.errors.length === 0,
      errors: checks.errors,
      warnings: [
        ...checks.warnings,
        "Web preflight 已完成；应用 Patch 后仍应运行 python scripts/okf.py lint。",
      ],
    },
  };
}
