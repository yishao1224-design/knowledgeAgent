import { runIngestAgent } from "@/lib/agent/ingest-agent";
import type { AgentModelInput } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as {
      repository?: string;
      branch?: string;
      title?: string;
      text?: string;
      sourceUrl?: string;
      model?: AgentModelInput;
    };
    if (!body.repository) return Response.json({ error: "请填写仓库地址。" }, { status: 400 });
    const result = await runIngestAgent({
      repository: body.repository,
      branch: body.branch,
      model: body.model,
      material: {
        title: body.title || "",
        text: body.text || "",
        sourceUrl: body.sourceUrl,
      },
    });
    return Response.json(result, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("knowledge ingest failed", error);
    const message = error instanceof Error ? error.message : "Ingest 预览生成失败。";
    return Response.json({ error: message }, { status: 400 });
  }
}
