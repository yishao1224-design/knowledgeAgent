"use client";

import {
  ArrowRight,
  BookOpen,
  Bot,
  Check,
  ChevronDown,
  CircleAlert,
  Clock3,
  Download,
  ExternalLink,
  FileCode2,
  FileText,
  GitBranch,
  GitCommitHorizontal,
  GitPullRequest,
  KeyRound,
  LoaderCircle,
  Menu,
  PanelLeftClose,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  Workflow,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import type {
  AskResponse,
  Citation,
  IngestPreview,
  KnowledgePage,
  KnowledgeStatus,
  RepositorySnapshot,
  WorkflowTrace,
} from "@/lib/types";

const DEFAULT_REPOSITORY = "https://github.com/yishao1224-design/knowledgeAgent";
const DEFAULT_MODEL_ENDPOINT = "https://api.openai.com/v1";
const DEFAULT_MODEL = "gpt-4.1-mini";

const SECTION_LABELS: Record<string, string> = {
  root: "Bundle",
  concepts: "Concepts",
  entities: "Entities",
  comparisons: "Comparisons",
  queries: "Queries",
  sources: "Sources",
  archive: "Archive",
};

const STATUS_LABELS: Record<KnowledgeStatus, string> = {
  active: "Active",
  draft: "Draft",
  needs_review: "Needs review",
  deprecated: "Deprecated",
  archived: "Archived",
  source: "Source",
  unknown: "Unknown",
};

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  workflow?: WorkflowTrace;
};

async function requestJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) throw new Error(payload.error || "请求失败，请稍后重试。");
  return payload;
}

function StatusPill({ status }: { status: KnowledgeStatus }) {
  return (
    <span className="status-pill" data-status={status}>
      <span aria-hidden="true" />
      {STATUS_LABELS[status]}
    </span>
  );
}

function EmptyWorkspace({ onOpen }: { onOpen: () => void }) {
  return (
    <main className="empty-workspace">
      <div className="empty-orbit orbit-one" />
      <div className="empty-orbit orbit-two" />
      <section className="empty-copy">
        <div className="eyebrow"><Sparkles size={14} /> Git-backed knowledge, without the database</div>
        <h1>Open a knowledge base.<br /><span>See what it knows.</span></h1>
        <p>
          Every action starts from a fresh, depth-one clone. Browse the OKF bundle,
          ask grounded questions, and turn new material into a reviewable patch.
        </p>
        <button className="primary-button hero-button" onClick={onOpen}>
          Open repository <ArrowRight size={17} />
        </button>
        <div className="empty-notes">
          <span><Check size={14} /> No database</span>
          <span><Check size={14} /> No shared repo cache</span>
          <span><Check size={14} /> Patch-first ingest</span>
        </div>
      </section>
      <aside className="empty-card" aria-label="How it works">
        <div className="empty-card-head">
          <div className="repo-mark"><GitBranch size={19} /></div>
          <div>
            <strong>Each execution</strong>
            <span>isolated &amp; traceable</span>
          </div>
        </div>
        <ol>
          <li><span>01</span><div><strong>Shallow clone</strong><small>depth 1 · single branch</small></div></li>
          <li><span>02</span><div><strong>Load fixed skill</strong><small>versioned · hash verified</small></div></li>
          <li><span>03</span><div><strong>Let Pi investigate</strong><small>search · read · answer</small></div></li>
          <li><span>04</span><div><strong>Dispose workspace</strong><small>nothing retained server-side</small></div></li>
        </ol>
      </aside>
    </main>
  );
}

export default function Home() {
  const [repository, setRepository] = useState(DEFAULT_REPOSITORY);
  const [branch, setBranch] = useState("");
  const [modelEndpoint, setModelEndpoint] = useState(DEFAULT_MODEL_ENDPOINT);
  const [modelName, setModelName] = useState(DEFAULT_MODEL);
  const [apiKey, setApiKey] = useState("");
  const [snapshot, setSnapshot] = useState<RepositorySnapshot | null>(null);
  const [selectedPath, setSelectedPath] = useState("");
  const [query, setQuery] = useState("");
  const [importOpen, setImportOpen] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentMode, setAgentMode] = useState<"ask" | "ingest">("ask");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "打开仓库后，我会基于每次新鲜的浅克隆回答问题，并把结论关联回具体知识页面。",
    },
  ]);
  const [ingestTitle, setIngestTitle] = useState("");
  const [ingestUrl, setIngestUrl] = useState("");
  const [ingestText, setIngestText] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [preview, setPreview] = useState<IngestPreview | null>(null);
  const [patchOpen, setPatchOpen] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const savedRepo = window.localStorage.getItem("kb-workspace-repository");
    const savedBranch = window.localStorage.getItem("kb-workspace-branch");
    const savedEndpoint = window.localStorage.getItem("kb-workspace-model-endpoint");
    const savedModel = window.localStorage.getItem("kb-workspace-model-name");
    if (savedRepo) setRepository(savedRepo);
    if (savedBranch) setBranch(savedBranch);
    if (savedEndpoint) setModelEndpoint(savedEndpoint);
    if (savedModel) setModelName(savedModel);
  }, []);

  const selectedPage = snapshot?.pages.find((page) => page.bundlePath === selectedPath) || null;
  const visiblePages = useMemo(() => {
    if (!snapshot) return [];
    const term = query.trim().toLowerCase();
    if (!term) return snapshot.pages;
    return snapshot.pages.filter((page) =>
      [page.title, page.description, page.type, page.tags.join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [snapshot, query]);
  const groupedPages = useMemo(() => {
    const groups = new Map<string, KnowledgePage[]>();
    for (const page of visiblePages) {
      const bucket = groups.get(page.section) || [];
      bucket.push(page);
      groups.set(page.section, bucket);
    }
    return groups;
  }, [visiblePages]);

  async function importRepository() {
    setLoading(true);
    setError("");
    setPreview(null);
    try {
      const result = await requestJson<RepositorySnapshot>("/api/repository", { repository, branch });
      setSnapshot(result);
      const first = result.pages.find((page) => page.section === "concepts") || result.pages[0];
      setSelectedPath(first?.bundlePath || "");
      setRepository(result.repository);
      setBranch(result.branch === "HEAD" ? "" : result.branch);
      window.localStorage.setItem("kb-workspace-repository", result.repository);
      window.localStorage.setItem("kb-workspace-branch", result.branch === "HEAD" ? "" : result.branch);
      window.localStorage.setItem("kb-workspace-model-endpoint", modelEndpoint.trim());
      window.localStorage.setItem("kb-workspace-model-name", modelName.trim());
      setImportOpen(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "仓库导入失败。");
    } finally {
      setLoading(false);
    }
  }

  async function askQuestion() {
    const clean = question.trim();
    if (!clean || !snapshot || asking) return;
    if (!apiKey.trim()) {
      setError("请先填写本次会话使用的模型 API Key。Key 只随 Agent 请求发送，不会保存。");
      setImportOpen(true);
      return;
    }
    const userMessage: Message = { id: crypto.randomUUID(), role: "user", text: clean };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setAsking(true);
    try {
      const result = await requestJson<AskResponse>("/api/ask", {
        repository,
        branch: snapshot.branch,
        question: clean,
        model: { baseUrl: modelEndpoint, model: modelName, apiKey },
      });
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", text: result.answer, citations: result.citations, workflow: result.workflow },
      ]);
    } catch (cause) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: `这次执行没有完成：${cause instanceof Error ? cause.message : "未知错误"}`,
        },
      ]);
    } finally {
      setAsking(false);
    }
  }

  async function createPreview() {
    if (!snapshot || ingesting) return;
    if (!apiKey.trim()) {
      setError("请先填写本次会话使用的模型 API Key。Key 只随 Agent 请求发送，不会保存。");
      setImportOpen(true);
      return;
    }
    setIngesting(true);
    setPreview(null);
    try {
      const result = await requestJson<IngestPreview>("/api/ingest", {
        repository,
        branch: snapshot.branch,
        title: ingestTitle,
        sourceUrl: ingestUrl,
        text: ingestText,
        model: { baseUrl: modelEndpoint, model: modelName, apiKey },
      });
      setPreview(result);
    } catch (cause) {
      setPreview({
        commit: "",
        branch: snapshot.branch,
        plan: [],
        files: [],
        patch: "",
        checks: { passed: false, errors: [cause instanceof Error ? cause.message : "生成失败。"], warnings: [] },
      });
    } finally {
      setIngesting(false);
    }
  }

  function downloadPatch() {
    if (!preview?.patch) return;
    const blob = new Blob([preview.patch], { type: "text/x-diff;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `kb-ingest-${Date.now()}.patch`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function selectBundleLink(href?: string) {
    if (!href?.startsWith("/")) return;
    const clean = href.split("#")[0];
    if (snapshot?.pages.some((page) => page.bundlePath === clean)) setSelectedPath(clean);
  }

  return (
    <div className="site-shell">
      <header className="topbar">
        <button className="brand" onClick={() => setImportOpen(true)} aria-label="Open repository dialog">
          <span className="brand-mark">K</span>
          <span><strong>Knowledge</strong><small>workspace</small></span>
        </button>
        <div className="repository-bar">
          <button className="mobile-menu" onClick={() => setSidebarOpen((value) => !value)} aria-label="Toggle navigation">
            <Menu size={18} />
          </button>
          {snapshot ? (
            <>
              <button className="repo-current" onClick={() => setImportOpen(true)}>
                <GitBranch size={16} />
                <span>{snapshot.repository.replace(/^https:\/\//, "")}</span>
                <ChevronDown size={14} />
              </button>
              <span className="commit-chip"><GitCommitHorizontal size={14} /> {snapshot.commit.slice(0, 8)}</span>
            </>
          ) : (
            <button className="repo-current muted" onClick={() => setImportOpen(true)}>
              <GitBranch size={16} /> Choose a repository
            </button>
          )}
        </div>
        <div className="top-actions">
          {snapshot && (
            <>
              <span className="fresh-clone"><ShieldCheck size={15} /> depth 1</span>
              <button className="icon-button" onClick={importRepository} disabled={loading} aria-label="Refresh from a new shallow clone">
                <RefreshCw size={16} className={loading ? "spin" : ""} />
              </button>
            </>
          )}
          <button className="icon-button" onClick={() => setImportOpen(true)} aria-label="Configure Pi model">
            <KeyRound size={16} />
          </button>
          <a className="icon-button" href="https://github.com/yishao1224-design/knowledgeAgent" target="_blank" rel="noreferrer" aria-label="Open source repository">
            <ExternalLink size={16} />
          </a>
        </div>
      </header>

      {!snapshot ? (
        <EmptyWorkspace onOpen={() => setImportOpen(true)} />
      ) : (
        <main className={`workspace ${sidebarOpen ? "" : "sidebar-collapsed"}`}>
          <aside className="library-panel">
            <div className="panel-heading">
              <div><span className="panel-kicker">LIBRARY</span><strong>{snapshot.stats.pages} pages</strong></div>
              <button className="icon-button subtle" onClick={() => setSidebarOpen(false)} aria-label="Collapse library"><PanelLeftClose size={17} /></button>
            </div>
            <label className="search-box">
              <Search size={15} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search knowledge…" />
              {query && <button onClick={() => setQuery("")} aria-label="Clear search"><X size={13} /></button>}
            </label>
            <nav className="page-tree" aria-label="Knowledge pages">
              {[...groupedPages.entries()].map(([section, pages]) => (
                <section className="tree-section" key={section}>
                  <div className="tree-section-title">
                    <span>{SECTION_LABELS[section] || section}</span><small>{pages.length}</small>
                  </div>
                  {pages.map((page) => (
                    <button
                      key={page.bundlePath}
                      className={selectedPath === page.bundlePath ? "tree-item active" : "tree-item"}
                      onClick={() => setSelectedPath(page.bundlePath)}
                    >
                      {page.type === "Source" ? <FileText size={15} /> : <BookOpen size={15} />}
                      <span>{page.title}</span>
                      {page.status === "needs_review" && <CircleAlert size={13} className="warn-icon" />}
                    </button>
                  ))}
                </section>
              ))}
              {!visiblePages.length && <div className="no-results">No pages match “{query}”.</div>}
            </nav>
            <div className="library-footer">
              <div><span>Concepts</span><strong>{snapshot.stats.concepts}</strong></div>
              <div><span>Sources</span><strong>{snapshot.stats.sources}</strong></div>
              <div><span>Review</span><strong>{snapshot.stats.needsReview}</strong></div>
            </div>
          </aside>

          <article className="document-panel">
            {!sidebarOpen && (
              <button className="reopen-sidebar" onClick={() => setSidebarOpen(true)}><Menu size={16} /> Library</button>
            )}
            {selectedPage ? (
              <>
                <div className="document-breadcrumb">
                  <span>{SECTION_LABELS[selectedPage.section] || selectedPage.section}</span>
                  <span>/</span>
                  <code>{selectedPage.path.replace(/^kb\//, "")}</code>
                </div>
                <header className="document-header">
                  <div className="document-status-row">
                    <StatusPill status={selectedPage.status} />
                    {selectedPage.confidence && <span className="meta-chip">{selectedPage.confidence} confidence</span>}
                    {selectedPage.updated && <span className="meta-chip"><Clock3 size={13} /> {selectedPage.updated}</span>}
                  </div>
                  <h1>{selectedPage.title}</h1>
                  <p>{selectedPage.description}</p>
                  {(selectedPage.tags.length > 0 || selectedPage.sources.length > 0) && (
                    <div className="document-tags">
                      {selectedPage.tags.map((tag) => <span key={tag}>#{tag}</span>)}
                      {selectedPage.sources.length > 0 && <span>{selectedPage.sources.length} source{selectedPage.sources.length > 1 ? "s" : ""}</span>}
                    </div>
                  )}
                </header>
                <div className="markdown-body">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeSanitize]}
                    components={{
                      a: ({ href, children, ...props }) => (
                        <a
                          href={href}
                          {...props}
                          onClick={(event) => {
                            if (href?.startsWith("/")) {
                              event.preventDefault();
                              selectBundleLink(href);
                            }
                          }}
                        >
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {selectedPage.body}
                  </ReactMarkdown>
                </div>
              </>
            ) : (
              <div className="document-empty"><BookOpen size={28} /><p>Select a page from the library.</p></div>
            )}
          </article>

          <aside className="agent-panel">
            <div className="agent-heading">
              <div className="agent-avatar"><Bot size={18} /></div>
              <div><strong>Knowledge agent</strong><span>Pi Agent · fixed skills</span></div>
              <span className="online-dot" title="Ready" />
            </div>
            <div className="mode-switch" role="tablist" aria-label="Agent mode">
              <button className={agentMode === "ask" ? "active" : ""} onClick={() => setAgentMode("ask")} role="tab">Ask</button>
              <button className={agentMode === "ingest" ? "active" : ""} onClick={() => setAgentMode("ingest")} role="tab">Ingest</button>
            </div>

            {agentMode === "ask" ? (
              <>
                <div className="message-list">
                  {messages.map((message) => (
                    <div className={`message ${message.role}`} key={message.id}>
                      {message.role === "assistant" && <div className="message-mark"><Sparkles size={13} /></div>}
                      <div className="message-bubble">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{message.text}</ReactMarkdown>
                        {message.citations && message.citations.length > 0 && (
                          <div className="citation-list">
                            {message.citations.slice(0, 3).map((citation, index) => (
                              <button key={citation.path} onClick={() => setSelectedPath(citation.path)}>
                                <span>{index + 1}</span><div><strong>{citation.title}</strong><small>{citation.path}</small></div>
                              </button>
                            ))}
                          </div>
                        )}
                        {message.workflow && (
                          <div className="workflow-trace" aria-label="Pi Agent execution trace">
                            <div><Workflow size={12} /><strong>Pi · {message.workflow.model}</strong><span>{message.workflow.runtime?.version.replace("knowledge-agent-", "fixed ") || `${message.workflow.steps.length} actions`}</span></div>
                            <ol>
                              {message.workflow.steps.map((step) => (
                                <li key={step.node}><Check size={10} /><code>{step.node}</code><span>{step.durationMs}ms</span></li>
                              ))}
                            </ol>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {asking && <div className="agent-thinking"><LoaderCircle size={15} className="spin" /> Pi is choosing and reading files…</div>}
                </div>
                <div className="ask-composer">
                  <textarea
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void askQuestion();
                      }
                    }}
                    placeholder="Ask this knowledge base…"
                    rows={3}
                  />
                  <div><span>↵ to send · fresh clone</span><button onClick={askQuestion} disabled={!question.trim() || asking} aria-label="Send question"><Send size={15} /></button></div>
                </div>
              </>
            ) : (
              <div className="ingest-panel">
                {!preview ? (
                  <>
                    <div className="ingest-intro"><GitPullRequest size={20} /><div><strong>Create a reviewable patch</strong><p>Capture evidence, draft a concept, update index and log.</p></div></div>
                    <label>Title<input value={ingestTitle} onChange={(event) => setIngestTitle(event.target.value)} placeholder="What is this material about?" /></label>
                    <label>Source URL <span>optional</span><input value={ingestUrl} onChange={(event) => setIngestUrl(event.target.value)} placeholder="https://…" /></label>
                    <label className="content-label">Content
                      <textarea value={ingestText} onChange={(event) => setIngestText(event.target.value)} placeholder="Paste Markdown, notes, or extracted source text…" rows={9} />
                    </label>
                    <input
                      ref={fileInput}
                      type="file"
                      accept=".md,.txt,text/plain,text/markdown"
                      hidden
                      onChange={async (event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        setIngestTitle((current) => current || file.name.replace(/\.(md|txt)$/i, ""));
                        setIngestText(await file.text());
                      }}
                    />
                    <div className="ingest-actions">
                      <button className="secondary-button" onClick={() => fileInput.current?.click()}><Upload size={15} /> Upload text</button>
                      <button className="primary-button" onClick={createPreview} disabled={ingesting || !ingestTitle.trim() || ingestText.trim().length < 40}>
                        {ingesting ? <LoaderCircle size={15} className="spin" /> : <Sparkles size={15} />}
                        Generate plan
                      </button>
                    </div>
                    <p className="ingest-footnote"><ShieldCheck size={13} /> Existing source captures are never modified.</p>
                  </>
                ) : (
                  <div className="preview-panel">
                    <div className={preview.checks.passed ? "check-banner passed" : "check-banner failed"}>
                      {preview.checks.passed ? <Check size={18} /> : <CircleAlert size={18} />}
                      <div><strong>{preview.checks.passed ? "Preflight passed" : "Needs attention"}</strong><span>{preview.commit ? `based on ${preview.commit.slice(0, 8)}` : "preview not generated"}</span></div>
                    </div>
                    {preview.workflow && (
                      <div className="ingest-workflow">
                        <span className="preview-label"><Workflow size={12} /> PI AGENT · {preview.workflow.runtime?.version.replace("knowledge-agent-", "fixed ") || preview.workflow.model}</span>
                        {preview.workflow.steps.map((step) => (
                          <div key={step.node}><Check size={11} /><code>{step.node}</code><span>{step.durationMs}ms</span></div>
                        ))}
                      </div>
                    )}
                    {preview.checks.errors.map((item) => <p className="preview-error" key={item}>{item}</p>)}
                    {preview.plan.length > 0 && <>
                      <span className="preview-label">EXECUTION PLAN</span>
                      <ol className="plan-list">{preview.plan.map((item, index) => <li key={item}><span>{index + 1}</span>{item}</li>)}</ol>
                      <span className="preview-label">FILES</span>
                      <div className="changed-files">{preview.files.map((file) => <div key={file.path}><FileCode2 size={14} /><code>{file.path}</code><span>{file.action}</span></div>)}</div>
                      <button className="patch-toggle" onClick={() => setPatchOpen((value) => !value)}>{patchOpen ? "Hide patch" : "Inspect patch"}<ChevronDown size={14} className={patchOpen ? "rotated" : ""} /></button>
                      {patchOpen && <pre className="patch-view">{preview.patch}</pre>}
                      <div className="preview-actions">
                        <button className="secondary-button" onClick={() => { setPreview(null); setPatchOpen(false); }}>Back</button>
                        <button className="primary-button" onClick={downloadPatch}><Download size={15} /> Download patch</button>
                      </div>
                    </>}
                  </div>
                )}
              </div>
            )}
          </aside>
        </main>
      )}

      {importOpen && (
        <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && snapshot) setImportOpen(false); }}>
          <section className="repo-dialog" role="dialog" aria-modal="true" aria-labelledby="repo-dialog-title">
            {snapshot && <button className="dialog-close" onClick={() => setImportOpen(false)} aria-label="Close"><X size={17} /></button>}
            <div className="dialog-icon"><GitBranch size={22} /></div>
            <span className="panel-kicker">NEW EXECUTION</span>
            <h2 id="repo-dialog-title">Open an OKF repository</h2>
            <p>Every Pi Agent run starts with a brand-new depth-one clone and a hash-verified fixed workflow skill. Nothing is cached or shared with another user.</p>
            <label>Repository URL<input value={repository} onChange={(event) => setRepository(event.target.value)} placeholder="https://github.com/owner/repo" /></label>
            <label>Branch <span>optional</span><input value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="default branch" /></label>
            <div className="agent-config-heading"><KeyRound size={13} /><span>PI AGENT MODEL</span></div>
            <div className="agent-config-row">
              <label>OpenAI-compatible Endpoint<input value={modelEndpoint} onChange={(event) => setModelEndpoint(event.target.value)} placeholder={DEFAULT_MODEL_ENDPOINT} spellCheck={false} /></label>
              <label>Model<input value={modelName} onChange={(event) => setModelName(event.target.value)} placeholder={DEFAULT_MODEL} spellCheck={false} /></label>
            </div>
            <label>API Key <span>session only</span><input type="password" value={apiKey} onChange={(event) => { setApiKey(event.target.value); setError(""); }} placeholder="sk-…" autoComplete="new-password" spellCheck={false} /></label>
            <p className="agent-key-note">API Key stays in this tab and is sent only with Ask or Ingest requests. It is never stored by the workspace.</p>
            {error && <div className="dialog-error"><CircleAlert size={15} /> {error}</div>}
            <button className="primary-button dialog-submit" onClick={importRepository} disabled={loading || !repository.trim()}>
              {loading ? <LoaderCircle size={16} className="spin" /> : <GitBranch size={16} />}
              {loading ? "Shallow cloning…" : "Open knowledge base"}
            </button>
            <div className="dialog-security"><ShieldCheck size={14} /><span>HTTPS only · public repositories · no submodules · 12 MB KB limit</span></div>
          </section>
        </div>
      )}
    </div>
  );
}
