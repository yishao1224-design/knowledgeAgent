import { fixedRuntimeAssets } from "@/lib/agent/fixed-runtime";

export const dynamic = "force-dynamic";

export async function GET() {
  const { manifest } = fixedRuntimeAssets();
  return Response.json(
    {
      ...manifest,
      activeRuntime: "cloudflare-worker",
      okfExecution: "typescript-adapter",
      pythonProcessAvailable: false,
    },
    { headers: { "Cache-Control": "public, max-age=300" } },
  );
}
