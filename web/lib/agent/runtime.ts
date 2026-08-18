import { Agent, type AgentTool } from "@earendil-works/pi-agent-core";
import type { AgentModelInput } from "../types";
import { createPiModels, resolveAgentModel, safeAgentError } from "./model";

const MAX_TURNS = 10;
const MAX_TOOL_CALLS = 24;
const RUN_TIMEOUT_MS = 50_000;

function finalAssistantText(agent: Agent): string {
  for (let index = agent.state.messages.length - 1; index >= 0; index -= 1) {
    const message = agent.state.messages[index];
    if (message.role !== "assistant") continue;
    const text = message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("\n")
      .trim();
    if (text) return text;
  }
  return "";
}

export async function runPiToolAgent(input: {
  model: AgentModelInput | undefined;
  systemPrompt: string;
  prompt: string;
  tools: AgentTool[];
}): Promise<{ answer: string; model: string }> {
  const config = resolveAgentModel(input.model);
  const { models, model } = createPiModels(config);
  const allowedTools = new Set(input.tools.map((tool) => tool.name));
  let turns = 0;
  let toolCalls = 0;

  const agent = new Agent({
    initialState: {
      systemPrompt: input.systemPrompt,
      model,
      thinkingLevel: "off",
      tools: input.tools,
      messages: [],
    },
    streamFn: models.streamSimple.bind(models),
    toolExecution: "sequential",
    maxRetryDelayMs: 5_000,
    beforeToolCall: async ({ toolCall }) => {
      if (!allowedTools.has(toolCall.name)) {
        return { block: true, reason: "This tool is not available in the isolated repository workspace." };
      }
      toolCalls += 1;
      if (toolCalls > MAX_TOOL_CALLS) {
        return { block: true, reason: "Repository tool-call budget exhausted.", terminate: true };
      }
      return undefined;
    },
    shouldStopAfterTurn: async () => {
      turns += 1;
      return turns >= MAX_TURNS;
    },
  });

  const timeout = setTimeout(() => agent.abort(), RUN_TIMEOUT_MS);
  try {
    await agent.prompt(input.prompt);
    if (agent.state.errorMessage) throw new Error(agent.state.errorMessage);
    const answer = finalAssistantText(agent);
    if (!answer) {
      throw new Error(
        turns >= MAX_TURNS
          ? "Pi Agent 达到本次执行的步骤上限，尚未生成最终答案。"
          : "Pi Agent 没有生成最终答案。",
      );
    }
    return { answer, model: config.modelId };
  } catch (error) {
    throw safeAgentError(error, config.apiKey);
  } finally {
    clearTimeout(timeout);
  }
}
