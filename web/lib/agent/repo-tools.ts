import type { AgentTool } from "@earendil-works/pi-agent-core";
import { Type } from "@earendil-works/pi-ai";
import type { LoadedRepository } from "../git-repository";
import type { WorkflowStep } from "../types";
import type { FixedSkillName } from "./fixed-runtime";

const MAX_LIST_RESULTS = 300;
const MAX_SEARCH_RESULTS = 40;
const MAX_READ_LINES = 240;
const MAX_READ_CHARS = 32_000;

export interface RepositoryToolRecorder {
  steps: WorkflowStep[];
  readPaths: Set<string>;
  searchedPaths: Set<string>;
  loadedSkill?: FixedSkillName;
}

function requireFixedSkill(recorder: RepositoryToolRecorder) {
  if (!recorder.loadedSkill) {
    throw new Error("The mandatory fixed workflow skill must be loaded before repository tools are used.");
  }
}

function normalizePath(input: string, repository: LoadedRepository): string {
  let path = input.trim().replace(/\\/g, "/").replace(/^\.\//, "");
  if (path.startsWith("/")) path = `kb${path}`;
  if (!path.startsWith("kb/")) path = `kb/${path}`;
  if (path.includes("..") || !repository.files.has(path)) throw new Error(`知识库中不存在文件：${input}`);
  return path;
}

function normalizePrefix(input = ""): string {
  let prefix = input.trim().replace(/\\/g, "/").replace(/^\.\//, "").replace(/^\//, "");
  if (prefix && !prefix.startsWith("kb/")) prefix = `kb/${prefix}`;
  if (prefix.includes("..")) throw new Error("目录前缀不能包含 ..");
  return prefix;
}

function finishStep(recorder: RepositoryToolRecorder, node: string, label: string, startedAt: number) {
  recorder.steps.push({
    node,
    label,
    durationMs: Math.max(0, Math.round(performance.now() - startedAt)),
  });
}

const ListFilesParameters = Type.Object({
  prefix: Type.Optional(Type.String({ description: "Optional kb-relative directory prefix, such as concepts" })),
});

const SearchFilesParameters = Type.Object({
  query: Type.String({ minLength: 2, maxLength: 160, description: "Literal text to search for" }),
  prefix: Type.Optional(Type.String({ description: "Optional kb-relative directory prefix" })),
});

const ReadFileParameters = Type.Object({
  path: Type.String({ description: "Exact file path returned by list_files or search_files" }),
  startLine: Type.Optional(Type.Integer({ minimum: 1, description: "First line, starting at 1" })),
  endLine: Type.Optional(Type.Integer({ minimum: 1, description: "Last line, inclusive" })),
});

export function createReadOnlyRepositoryTools(
  repository: LoadedRepository,
  recorder: RepositoryToolRecorder,
): AgentTool[] {
  const listFiles: AgentTool<typeof ListFilesParameters, { count: number }> = {
    name: "list_files",
    label: "List knowledge files",
    description: "List Markdown files in the cloned kb directory. Use a prefix to narrow the result.",
    parameters: ListFilesParameters,
    execute: async (_toolCallId, params, signal) => {
      signal?.throwIfAborted();
      requireFixedSkill(recorder);
      const startedAt = performance.now();
      const prefix = normalizePrefix(params.prefix);
      const paths = [...repository.files.keys()]
        .filter((path) => !prefix || path.startsWith(prefix))
        .sort()
        .slice(0, MAX_LIST_RESULTS);
      finishStep(recorder, "list_files", prefix ? `List ${prefix}` : "List knowledge files", startedAt);
      return {
        content: [{ type: "text", text: paths.length ? paths.join("\n") : "No files matched this prefix." }],
        details: { count: paths.length },
      };
    },
  };

  const searchFiles: AgentTool<typeof SearchFilesParameters, { count: number; paths: string[] }> = {
    name: "search_files",
    label: "Search knowledge files",
    description: "Search for literal text across the cloned kb Markdown files and return matching lines.",
    parameters: SearchFilesParameters,
    execute: async (_toolCallId, params, signal) => {
      signal?.throwIfAborted();
      requireFixedSkill(recorder);
      const startedAt = performance.now();
      const query = params.query.trim();
      const prefix = normalizePrefix(params.prefix);
      const needle = query.toLocaleLowerCase();
      const matches: string[] = [];
      const paths = new Set<string>();

      for (const [path, content] of repository.files) {
        if (prefix && !path.startsWith(prefix)) continue;
        const lines = content.split("\n");
        for (let index = 0; index < lines.length; index += 1) {
          if (!lines[index].toLocaleLowerCase().includes(needle)) continue;
          paths.add(path);
          recorder.searchedPaths.add(path);
          matches.push(`${path}:${index + 1}: ${lines[index].trim().slice(0, 240)}`);
          if (matches.length >= MAX_SEARCH_RESULTS) break;
        }
        if (matches.length >= MAX_SEARCH_RESULTS) break;
      }

      finishStep(recorder, "search_files", `Search “${query.slice(0, 42)}”`, startedAt);
      return {
        content: [{ type: "text", text: matches.length ? matches.join("\n") : "No literal matches found." }],
        details: { count: matches.length, paths: [...paths] },
      };
    },
  };

  const readFile: AgentTool<typeof ReadFileParameters, { path: string; startLine: number; endLine: number }> = {
    name: "read_file",
    label: "Read knowledge file",
    description: `Read a line range from one cloned kb Markdown file. At most ${MAX_READ_LINES} lines are returned per call.`,
    parameters: ReadFileParameters,
    execute: async (_toolCallId, params, signal) => {
      signal?.throwIfAborted();
      requireFixedSkill(recorder);
      const startedAt = performance.now();
      const path = normalizePath(params.path, repository);
      const lines = (repository.files.get(path) || "").split("\n");
      const startLine = Math.min(params.startLine || 1, Math.max(1, lines.length));
      const requestedEnd = params.endLine || startLine + MAX_READ_LINES - 1;
      const endLine = Math.min(lines.length, Math.max(startLine, requestedEnd), startLine + MAX_READ_LINES - 1);
      const content = lines.slice(startLine - 1, endLine).join("\n").slice(0, MAX_READ_CHARS);
      recorder.readPaths.add(path);
      finishStep(recorder, "read_file", `Read ${path}:${startLine}-${endLine}`, startedAt);
      return {
        content: [{ type: "text", text: `[${path} lines ${startLine}-${endLine} of ${lines.length}]\n${content}` }],
        details: { path, startLine, endLine },
      };
    },
  };

  return [listFiles, searchFiles, readFile];
}

export function createRepositoryToolRecorder(): RepositoryToolRecorder {
  return { steps: [], readPaths: new Set(), searchedPaths: new Set() };
}
