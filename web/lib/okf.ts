import YAML from "yaml";
import type {
  KnowledgePage,
  KnowledgeStatus,
  RepositoryStats,
} from "./types";

const FRONTMATTER = /^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?/;
const MARKDOWN_LINK = /\[[^\]]*\]\(([^)\s]+)\)/g;

const STATUS_VALUES = new Set<KnowledgeStatus>([
  "active",
  "draft",
  "needs_review",
  "deprecated",
  "archived",
]);

type Meta = Record<string, unknown>;

function asString(value: unknown): string {
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  return value == null ? "" : String(value);
}

function asList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(asString).filter(Boolean);
  return value ? [asString(value)] : [];
}

function titleFromBody(body: string, fallback: string): string {
  const match = body.match(/^#\s+(.+)$/m);
  return match?.[1]?.trim() || fallback;
}

function descriptionFromBody(body: string): string {
  const prose = body
    .replace(/^---[\s\S]*?---\s*/m, "")
    .replace(/^#{1,6}\s+.*$/gm, "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\[[^\]]+\]\([^)]+\)/g, "$1")
    .split(/\n\s*\n/)
    .map((line) => line.replace(/^[-*>\s]+/, "").trim())
    .find((line) => line.length > 20);
  return prose?.slice(0, 180) || "No description provided.";
}

export function splitFrontmatter(text: string): { meta: Meta; body: string } {
  const match = text.match(FRONTMATTER);
  if (!match) return { meta: {}, body: text };
  try {
    const parsed = YAML.parse(match[1]);
    return {
      meta: parsed && typeof parsed === "object" ? (parsed as Meta) : {},
      body: text.slice(match[0].length),
    };
  } catch {
    return { meta: {}, body: text.slice(match[0].length) };
  }
}

export function parseKnowledgePage(path: string, text: string): KnowledgePage {
  const { meta, body } = splitFrontmatter(text);
  const relative = path.replace(/^kb\//, "");
  const parts = relative.split("/");
  const section = parts.length > 1 ? parts[0] : "root";
  const fallback = parts.at(-1)?.replace(/\.md$/i, "") || "Untitled";
  const rawStatus = asString(meta.status).toLowerCase();
  const type = asString(meta.type) || (section === "sources" ? "Source" : "Page");
  const status: KnowledgeStatus =
    type === "Source"
      ? "source"
      : STATUS_VALUES.has(rawStatus as KnowledgeStatus)
        ? (rawStatus as KnowledgeStatus)
        : "unknown";
  const links = Array.from(body.matchAll(MARKDOWN_LINK), (match) => match[1])
    .filter((link) => link.startsWith("/") && link.endsWith(".md"));

  return {
    path,
    bundlePath: `/${relative}`,
    title: asString(meta.title) || titleFromBody(body, fallback),
    description: asString(meta.description) || descriptionFromBody(body),
    type,
    status,
    confidence: asString(meta.confidence) || undefined,
    updated: asString(meta.updated || meta.ingested) || undefined,
    reviewAfter: asString(meta.review_after) || undefined,
    tags: asList(meta.tags),
    sources: asList(meta.sources),
    section,
    body,
    links: [...new Set(links)],
  };
}

export function calculateStats(pages: KnowledgePage[]): RepositoryStats {
  const byStatus: Record<string, number> = {};
  for (const page of pages) {
    byStatus[page.status] = (byStatus[page.status] || 0) + 1;
  }
  return {
    pages: pages.length,
    concepts: pages.filter((page) => page.type !== "Source" && page.type !== "Schema").length,
    sources: pages.filter((page) => page.type === "Source").length,
    needsReview: pages.filter((page) => page.status === "needs_review").length,
    byStatus,
  };
}

const SECTION_ORDER = ["concepts", "entities", "comparisons", "queries", "archive", "sources"];

export function generateIndex(pages: KnowledgePage[]): string {
  const grouped = new Map<string, KnowledgePage[]>();
  for (const page of pages) {
    const bucket = grouped.get(page.section) || [];
    bucket.push(page);
    grouped.set(page.section, bucket);
  }

  const lines = ["---", 'okf_version: "0.1"', "---", "", "# Bundle Index", ""];
  const roots = (grouped.get("root") || []).sort((a, b) => a.title.localeCompare(b.title));
  for (const page of roots) {
    lines.push(`* [${page.title}](${page.bundlePath.slice(1)}) - ${page.description}`);
  }

  const remaining = [...grouped.keys()].filter((key) => key !== "root");
  const sections = [
    ...SECTION_ORDER.filter((section) => remaining.includes(section)),
    ...remaining.filter((section) => !SECTION_ORDER.includes(section)).sort(),
  ];
  for (const section of sections) {
    lines.push("", `# ${section[0].toUpperCase()}${section.slice(1)}`, "");
    for (const page of (grouped.get(section) || []).sort((a, b) => a.title.localeCompare(b.title))) {
      const badge = ["needs_review", "deprecated", "archived"].includes(page.status)
        ? ` *(${page.status})*`
        : "";
      lines.push(`* [${page.title}](${page.bundlePath.slice(1)}) - ${page.description}${badge}`);
    }
  }
  return `${lines.join("\n")}\n`;
}

export function updateLog(log: string, entry: string, date: string): string {
  const heading = `## ${date}`;
  const normalized = log || "# Bundle Update Log\n";
  if (normalized.includes(heading)) {
    return normalized.replace(heading, `${heading}\n* ${entry}`);
  }
  const lines = normalized.split(/\r?\n/);
  const h1 = Math.max(0, lines.findIndex((line) => line.startsWith("# ")));
  lines.splice(h1 + 1, 0, "", heading, `* ${entry}`);
  return `${lines.join("\n").replace(/\n+$/, "")}\n`;
}

export function validateBundle(pages: KnowledgePage[]): { errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  for (const page of pages) {
    if (!page.title) errors.push(`${page.bundlePath}: missing title`);
    if (!page.type) errors.push(`${page.bundlePath}: missing type`);
    if (page.type !== "Source" && page.type !== "Schema" && page.status === "unknown") {
      errors.push(`${page.bundlePath}: missing or invalid lifecycle status`);
    }
    if (page.status === "active" && !page.reviewAfter && page.type !== "Schema") {
      errors.push(`${page.bundlePath}: active page is missing review_after`);
    }
    if (page.status === "needs_review") warnings.push(`${page.bundlePath}: needs review`);
  }
  return { errors, warnings };
}
