export type KnowledgeStatus =
  | "active"
  | "draft"
  | "needs_review"
  | "deprecated"
  | "archived"
  | "source"
  | "unknown";

export interface KnowledgePage {
  path: string;
  bundlePath: string;
  title: string;
  description: string;
  type: string;
  status: KnowledgeStatus;
  confidence?: string;
  updated?: string;
  reviewAfter?: string;
  tags: string[];
  sources: string[];
  section: string;
  body: string;
  links: string[];
}

export interface RepositoryStats {
  pages: number;
  concepts: number;
  sources: number;
  needsReview: number;
  byStatus: Record<string, number>;
}

export interface RepositorySnapshot {
  repository: string;
  branch: string;
  commit: string;
  clonedAt: string;
  pages: KnowledgePage[];
  stats: RepositoryStats;
  warnings: string[];
}

export interface Citation {
  path: string;
  title: string;
  status: KnowledgeStatus;
  confidence?: string;
  excerpt: string;
}

export interface WorkflowStep {
  node: string;
  label: string;
  durationMs: number;
}

export interface WorkflowTrace {
  engine: "pi";
  mode: "query" | "ingest";
  model: string;
  steps: WorkflowStep[];
  runtime?: {
    version: string;
    skill: "kb-query" | "kb-ingest";
    skillHash: string;
    okfScriptHash: string;
    okfExecution: "typescript-adapter" | "python";
  };
}

export interface AgentModelInput {
  baseUrl?: string;
  model?: string;
  apiKey?: string;
}

export interface AskResponse {
  answer: string;
  commit: string;
  branch: string;
  citations: Citation[];
  workflow?: WorkflowTrace;
}

export interface IngestPreview {
  commit: string;
  branch: string;
  plan: string[];
  files: Array<{ path: string; action: "create" | "update" }>;
  patch: string;
  checks: {
    passed: boolean;
    errors: string[];
    warnings: string[];
  };
  workflow?: WorkflowTrace;
}
