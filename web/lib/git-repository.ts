import git from "isomorphic-git";
import http from "isomorphic-git/http/web";
import { Volume } from "memfs";
import { calculateStats, parseKnowledgePage, validateBundle } from "./okf";
import type { KnowledgePage, RepositorySnapshot } from "./types";

const MAX_KB_FILES = 1_200;
const MAX_FILE_BYTES = 1_000_000;
const MAX_KB_BYTES = 12_000_000;
const ALLOWED_HOSTS = new Set(["github.com", "gitlab.com", "bitbucket.org", "gitee.com"]);

export interface LoadedRepository extends RepositorySnapshot {
  files: Map<string, string>;
}

export function normalizeRepositoryUrl(input: string): string {
  let url: URL;
  try {
    url = new URL(input.trim());
  } catch {
    throw new Error("请输入完整的 HTTPS Git 仓库地址。");
  }
  if (url.protocol !== "https:") throw new Error("目前只支持 HTTPS Git 仓库。");
  if (url.username || url.password) throw new Error("仓库地址中不能包含用户名或凭证。");
  if (!ALLOWED_HOSTS.has(url.hostname.toLowerCase())) {
    throw new Error("当前版本支持 GitHub、GitLab、Bitbucket 和 Gitee 公共仓库。");
  }
  if (url.pathname.split("/").filter(Boolean).length < 2) throw new Error("仓库地址缺少 owner 或 repo。");
  url.hash = "";
  url.search = "";
  url.pathname = url.pathname.replace(/\/$/, "");
  if (url.hostname === "github.com" && !url.pathname.endsWith(".git")) url.pathname += ".git";
  return url.toString().replace(/\/$/, "");
}

export async function shallowCloneRepository(
  repositoryInput: string,
  requestedBranch?: string,
): Promise<LoadedRepository> {
  const repository = normalizeRepositoryUrl(repositoryInput);
  const branch = requestedBranch?.trim() || undefined;
  if (branch && !/^[A-Za-z0-9._/-]+$/.test(branch)) throw new Error("分支名称格式不正确。");

  const volume = new Volume();
  const dir = "/workspace";
  await git.clone({
    fs: volume,
    http,
    dir,
    url: repository,
    ref: branch,
    singleBranch: true,
    depth: 1,
    noTags: true,
  });

  const resolvedBranch = (await git.currentBranch({ fs: volume, dir, fullname: false })) || branch || "HEAD";
  const commit = await git.resolveRef({ fs: volume, dir, ref: "HEAD" });
  const tracked = await git.listFiles({ fs: volume, dir });
  const kbFiles = tracked.filter((path) => path.startsWith("kb/") && path.endsWith(".md"));
  if (!kbFiles.includes("kb/SCHEMA.md")) {
    throw new Error("这个仓库还没有 OKF 知识库：未找到 kb/SCHEMA.md。");
  }
  if (!kbFiles.includes("kb/index.md") || !kbFiles.includes("kb/log.md")) {
    throw new Error("知识库不完整：需要 kb/index.md 和 kb/log.md。");
  }
  if (kbFiles.length > MAX_KB_FILES) throw new Error(`知识库文件超过 ${MAX_KB_FILES} 个，已停止加载。`);

  const files = new Map<string, string>();
  let totalBytes = 0;
  for (const path of kbFiles) {
    const bytes = (await volume.promises.readFile(`${dir}/${path}`)) as Uint8Array;
    if (bytes.byteLength > MAX_FILE_BYTES) throw new Error(`${path} 超过单文件大小限制。`);
    totalBytes += bytes.byteLength;
    if (totalBytes > MAX_KB_BYTES) throw new Error("知识库内容超过 12 MB，已停止加载。");
    files.set(path, new TextDecoder().decode(bytes));
  }

  const pages: KnowledgePage[] = [];
  for (const [path, text] of files) {
    if (path === "kb/index.md" || path === "kb/log.md") continue;
    pages.push(parseKnowledgePage(path, text));
  }
  pages.sort((a, b) => a.section.localeCompare(b.section) || a.title.localeCompare(b.title));
  const validation = validateBundle(pages);

  return {
    repository: repository.replace(/\.git$/, ""),
    branch: resolvedBranch,
    commit,
    clonedAt: new Date().toISOString(),
    pages,
    stats: calculateStats(pages),
    warnings: validation.warnings,
    files,
  };
}
