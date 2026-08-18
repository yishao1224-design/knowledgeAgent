import { shallowCloneRepository } from "@/lib/git-repository";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { repository?: string; branch?: string };
    if (!body.repository) return Response.json({ error: "请填写仓库地址。" }, { status: 400 });
    const result = await shallowCloneRepository(body.repository, body.branch);
    const { files: _files, ...snapshot } = result;
    void _files;
    return Response.json(snapshot, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("repository import failed", error);
    const message = error instanceof Error ? error.message : "仓库加载失败。";
    return Response.json({ error: message }, { status: 400 });
  }
}
