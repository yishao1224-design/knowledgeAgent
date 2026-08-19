import {
  createModels,
  createProvider,
  type Model,
  type MutableModels,
} from "@earendil-works/pi-ai";
import { openAICompletionsApi } from "@earendil-works/pi-ai/api/openai-completions.lazy";
import type { AgentModelInput, ModelConnectionTestResponse } from "../types";

const DEFAULT_BASE_URL = "https://api.openai.com/v1";
const DEFAULT_MODEL = "gpt-4.1-mini";

export interface ResolvedAgentModel {
  apiKey: string;
  baseUrl: string;
  modelId: string;
}

function publicHttpsUrl(value: string): string {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("模型 Endpoint 必须是完整的 HTTPS URL。");
  }
  if (url.protocol !== "https:") throw new Error("模型 Endpoint 仅支持 HTTPS。");
  if (url.username || url.password) throw new Error("模型 Endpoint 不能包含凭证。");
  if (url.search || url.hash) throw new Error("模型 Endpoint 不能包含 query 或 hash。");
  if (url.port && url.port !== "443") throw new Error("模型 Endpoint 仅支持标准 HTTPS 端口。");

  const hostname = url.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (
    hostname === "localhost" ||
    hostname.endsWith(".localhost") ||
    hostname.endsWith(".local") ||
    hostname.endsWith(".internal") ||
    hostname.includes(":") ||
    /^\d{1,3}(?:\.\d{1,3}){3}$/.test(hostname)
  ) {
    throw new Error("模型 Endpoint 必须使用公开域名。");
  }

  url.pathname = url.pathname.replace(/\/$/, "") || "/";
  return url.toString().replace(/\/$/, "");
}

export function resolveAgentModel(input?: AgentModelInput): ResolvedAgentModel {
  const apiKey = input?.apiKey?.trim() || "";
  const modelId = input?.model?.trim() || DEFAULT_MODEL;
  if (!apiKey) throw new Error("请填写本次会话使用的模型 API Key。");
  if (apiKey.length > 4_096) throw new Error("模型 API Key 格式不正确。");
  if (!/^[A-Za-z0-9._:/-]{1,160}$/.test(modelId)) throw new Error("模型名称格式不正确。");

  return {
    apiKey,
    baseUrl: publicHttpsUrl(input?.baseUrl?.trim() || DEFAULT_BASE_URL),
    modelId,
  };
}

export function createPiModels(config: ResolvedAgentModel): {
  models: MutableModels;
  model: Model<"openai-completions">;
} {
  const model: Model<"openai-completions"> = {
    id: config.modelId,
    name: config.modelId,
    api: "openai-completions",
    provider: "workspace-compatible",
    baseUrl: config.baseUrl,
    reasoning: false,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 128_000,
    maxTokens: 4_096,
    compat: {
      supportsStore: false,
      supportsDeveloperRole: false,
      supportsReasoningEffort: false,
      supportsStrictMode: false,
    },
  };

  const provider = createProvider({
    id: "workspace-compatible",
    name: "Workspace OpenAI-compatible endpoint",
    baseUrl: config.baseUrl,
    auth: {
      apiKey: {
        name: "Request-scoped API key",
        resolve: async () => ({ auth: { apiKey: config.apiKey }, source: "request" }),
      },
    },
    models: [model],
    api: openAICompletionsApi(),
  });
  const models = createModels();
  models.setProvider(provider);
  return { models, model };
}

export function safeAgentError(error: unknown, apiKey?: string): Error {
  const fallback = "Pi Agent 执行失败，请检查 Endpoint、模型名称和 API Key。";
  const raw = error instanceof Error ? error.message : typeof error === "string" ? error : fallback;
  const redacted = apiKey ? raw.split(apiKey).join("[redacted]") : raw;
  return new Error(redacted.slice(0, 600) || fallback);
}

export async function testAgentModelConnection(input?: AgentModelInput): Promise<ModelConnectionTestResponse> {
  let config: ResolvedAgentModel;
  try {
    config = resolveAgentModel(input);
  } catch (error) {
    return {
      ok: false,
      baseUrl: input?.baseUrl?.trim() || DEFAULT_BASE_URL,
      model: input?.model?.trim() || DEFAULT_MODEL,
      message: error instanceof Error ? error.message : "模型配置无效。",
    };
  }

  try {
    const response = await fetch(`${config.baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: config.modelId,
        messages: [{ role: "user", content: "Reply with OK." }],
        max_tokens: 1,
        stream: false,
      }),
    });
    if (response.ok) {
      return {
        ok: true,
        baseUrl: config.baseUrl,
        model: config.modelId,
        status: response.status,
        message: "模型连接测试成功。",
      };
    }

    const detail = (await response.text()).replace(config.apiKey, "[redacted]").slice(0, 300).trim();
    return {
      ok: false,
      baseUrl: config.baseUrl,
      model: config.modelId,
      status: response.status,
      message: detail ? `模型连接失败：${detail}` : `模型连接失败：HTTP ${response.status}`,
    };
  } catch (error) {
    return {
      ok: false,
      baseUrl: config.baseUrl,
      model: config.modelId,
      message: safeAgentError(error, config.apiKey).message,
    };
  }
}

export const DEFAULT_AGENT_MODEL = {
  baseUrl: DEFAULT_BASE_URL,
  model: DEFAULT_MODEL,
} as const;
