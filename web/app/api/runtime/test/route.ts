import { testAgentModelConnection } from "@/lib/agent/model";
import type { AgentModelInput } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const body = (await request.json()) as { model?: AgentModelInput };
  const result = await testAgentModelConnection(body.model);
  return Response.json(result, { headers: { "Cache-Control": "no-store" } });
}