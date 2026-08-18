import type { AskResponse, KnowledgePage } from "./types";

export interface RankedKnowledgePage {
  page: KnowledgePage;
  score: number;
}

const STOP_WORDS = new Set([
  "what", "when", "where", "which", "with", "from", "about", "this", "that",
  "什么", "怎么", "如何", "是否", "哪些", "一个", "这个", "那个", "知识库", "请问",
]);

const ZH_ALIASES: Array<[string, string[]]> = [
  ["知识生命周期", ["knowledge", "lifecycle"]],
  ["生命周期", ["lifecycle"]],
  ["知识库", ["knowledge", "bundle"]],
  ["状态", ["status", "state"]],
  ["摄取", ["ingest", "capture"]],
  ["导入", ["import", "adopt"]],
  ["来源", ["source", "citation"]],
  ["格式", ["format", "schema"]],
  ["校验", ["lint", "verify"]],
  ["审核", ["review"]],
  ["工具", ["tool", "toolchain"]],
];

function queryTerms(question: string): string[] {
  const lower = question.toLowerCase();
  const terms = new Set<string>();
  for (const word of lower.match(/[a-z0-9_-]{2,}/g) || []) {
    if (!STOP_WORDS.has(word)) terms.add(word);
  }
  for (const sequence of lower.match(/[\p{Script=Han}]{2,}/gu) || []) {
    if (!STOP_WORDS.has(sequence)) terms.add(sequence);
    for (let size = 2; size <= Math.min(4, sequence.length); size += 1) {
      for (let i = 0; i <= sequence.length - size; i += 1) terms.add(sequence.slice(i, i + size));
    }
  }
  for (const [phrase, aliases] of ZH_ALIASES) {
    if (lower.includes(phrase)) aliases.forEach((alias) => terms.add(alias));
  }
  return [...terms].filter((term) => !STOP_WORDS.has(term));
}

function occurrences(text: string, term: string): number {
  let count = 0;
  let cursor = 0;
  const haystack = text.toLowerCase();
  while ((cursor = haystack.indexOf(term, cursor)) !== -1) {
    count += 1;
    cursor += term.length;
    if (count >= 6) break;
  }
  return count;
}

function excerpt(page: KnowledgePage, terms: string[]): string {
  const paragraphs = page.body
    .replace(/```[\s\S]*?```/g, "")
    .replace(/^#{1,6}\s+.*$/gm, "")
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.replace(/\s+/g, " ").replace(/^[-*>\s]+/, "").trim())
    .filter((paragraph) => paragraph.length > 30);
  const best = paragraphs.find((paragraph) => terms.some((term) => paragraph.toLowerCase().includes(term)));
  return (best || page.description).slice(0, 240);
}

function trustLabel(page: KnowledgePage): string {
  if (page.status === "needs_review") return "可能过期";
  if (page.status === "draft") return "尚未验证";
  if (page.status === "deprecated") return "已弃用";
  if (page.tags.includes("contested")) return "存在争议";
  return page.confidence ? `${page.confidence} confidence` : "已收录";
}

export function retrieveRelevantPages(
  pages: KnowledgePage[],
  question: string,
): RankedKnowledgePage[] {
  const terms = queryTerms(question);
  return pages
    .filter((page) => page.type !== "Source" && page.status !== "archived")
    .map((page) => {
      const score = terms.reduce(
        (sum, term) =>
          sum +
          occurrences(page.title, term) * 8 +
          occurrences(page.description, term) * 4 +
          occurrences(page.tags.join(" "), term) * 3 +
          occurrences(page.body, term),
        0,
      );
      return { page, score };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
}

export function synthesizeAnswer(
  scored: RankedKnowledgePage[],
  question: string,
  commit: string,
  branch: string,
): AskResponse {
  const terms = queryTerms(question);

  if (!scored.length) {
    return {
      answer: `当前知识库中没有找到足以回答“${question}”的内容。可以换一个更具体的关键词，或者通过 Ingest 补充相关资料。`,
      commit,
      branch,
      citations: [],
    };
  }

  const primary = scored.slice(0, 3).map(({ page }) => {
    const text = excerpt(page, terms);
    return `- **${page.title}**（${trustLabel(page)}）：${text}  \n  来源：${page.bundlePath}`;
  });
  const cautions = scored
    .map(({ page }) => page)
    .filter((page) => page.status !== "active" || page.tags.includes("contested"))
    .map((page) => `${page.title} 为 ${trustLabel(page)}`);

  return {
    answer: [
      `基于本次浅克隆的知识库，和问题最相关的是以下内容：`,
      "",
      ...primary,
      ...(cautions.length ? ["", `可信度提示：${cautions.join("；")}。`] : []),
      "",
      `回答对应 commit \`${commit.slice(0, 8)}\`。`,
    ].join("\n"),
    commit,
    branch,
    citations: scored.map(({ page }) => ({
      path: page.bundlePath,
      title: page.title,
      status: page.status,
      confidence: page.confidence,
      excerpt: excerpt(page, terms),
    })),
  };
}

export function answerQuestion(
  pages: KnowledgePage[],
  question: string,
  commit: string,
  branch: string,
): AskResponse {
  return synthesizeAnswer(retrieveRelevantPages(pages, question), question, commit, branch);
}
