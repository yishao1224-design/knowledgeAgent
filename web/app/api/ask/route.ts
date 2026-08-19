import { runQueryAgent } from "@/lib/agent/query-agent";
import type { AgentModelInput, RepositoryAuthInput } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as {
      repository?: string;
      branch?: string;
      auth?: RepositoryAuthInput;
      question?: string;
      model?: AgentModelInput;
    };
    if (!body.repository || !body.question?.trim()) {
      return Response.json({ error: "仓库地址和问题不能为空。" }, { status: 400 });
    }
    const result = await runQueryAgent({
      repository: body.repository,
      branch: body.branch,
      auth: body.auth,
      question: body.question.trim(),
      model: body.model,
    });
    return Response.json(result, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("knowledge query failed", error);
    const message = error instanceof Error ? error.message : "提问执行失败。";
    return Response.json({ error: message }, { status: 400 });
  }
}
