import type { AgentTool } from "@earendil-works/pi-agent-core";
import { Type } from "@earendil-works/pi-ai";
import type { WorkflowStep } from "../types";
import {
  FIXED_INGEST_SKILL,
  FIXED_OKF_SCRIPT,
  FIXED_QUERY_SKILL,
  FIXED_RUNTIME_MANIFEST,
} from "./fixed-runtime.generated";

export type FixedSkillName = "kb-query" | "kb-ingest";

interface SkillLoadRecorder {
  steps: WorkflowStep[];
  loadedSkill?: FixedSkillName;
}

const LoadSkillParameters = Type.Object({});

const WORKER_ADAPTER: Record<FixedSkillName, string> = {
  "kb-query": `Runtime adapter for this deployment:
- The repository tools are read-only and restricted to kb/.
- Follow Steps 0-2 of the fixed skill for every answer.
- Step 3 (filing a Query page) is disabled until the user explicitly starts an ingest operation.
- Do not request shell execution.`,
  "kb-ingest": `Runtime adapter for this deployment:
- Follow the fixed skill's orientation, duplicate search, trust, and lifecycle rules.
- The draft_ingest tool creates the immutable source, draft page, index/log updates, validation, and reviewable patch in one ephemeral operation.
- The original okf.py is bundled and hash-verified, but this Cloudflare Worker cannot start a Python process. The TypeScript adapter performs the current mechanical checks.
- Never claim the patch was applied or pushed.`,
};

function skillText(name: FixedSkillName): string {
  return name === "kb-query" ? FIXED_QUERY_SKILL : FIXED_INGEST_SKILL;
}

export function createFixedSkillTool(
  name: FixedSkillName,
  recorder: SkillLoadRecorder,
): AgentTool<typeof LoadSkillParameters, {
  skill: FixedSkillName;
  runtimeVersion: string;
  skillHash: string;
  okfScriptHash: string;
}> {
  const skillPath = `skills/${name}/SKILL.md` as const;
  return {
    name: "load_skill",
    label: `Load fixed ${name} skill`,
    description: `Mandatory first action. Load the trusted, fixed-version ${name} workflow before accessing repository files.`,
    parameters: LoadSkillParameters,
    executionMode: "sequential",
    execute: async (_toolCallId, _params, signal) => {
      signal?.throwIfAborted();
      const startedAt = performance.now();
      recorder.loadedSkill = name;
      recorder.steps.push({
        node: "load_skill",
        label: `Load fixed ${name} · ${FIXED_RUNTIME_MANIFEST.runtimeVersion}`,
        durationMs: Math.max(0, Math.round(performance.now() - startedAt)),
      });
      return {
        content: [{
          type: "text",
          text: [
            `Fixed runtime: ${FIXED_RUNTIME_MANIFEST.runtimeVersion}`,
            `Source commit: ${FIXED_RUNTIME_MANIFEST.sourceCommit}`,
            `Skill SHA-256: ${FIXED_RUNTIME_MANIFEST.files[skillPath]}`,
            `okf.py SHA-256: ${FIXED_RUNTIME_MANIFEST.files["scripts/okf.py"]}`,
            "",
            "--- BEGIN FIXED SKILL ---",
            skillText(name),
            "--- END FIXED SKILL ---",
            "",
            WORKER_ADAPTER[name],
          ].join("\n"),
        }],
        details: {
          skill: name,
          runtimeVersion: FIXED_RUNTIME_MANIFEST.runtimeVersion,
          skillHash: FIXED_RUNTIME_MANIFEST.files[skillPath],
          okfScriptHash: FIXED_RUNTIME_MANIFEST.files["scripts/okf.py"],
        },
      };
    },
  };
}

export function fixedRuntimeTrace(name: FixedSkillName) {
  return {
    version: FIXED_RUNTIME_MANIFEST.runtimeVersion,
    skill: name,
    skillHash: FIXED_RUNTIME_MANIFEST.files[`skills/${name}/SKILL.md`],
    okfScriptHash: FIXED_RUNTIME_MANIFEST.files["scripts/okf.py"],
    okfExecution: "typescript-adapter" as const,
  };
}

export function fixedRuntimeAssets() {
  return {
    manifest: FIXED_RUNTIME_MANIFEST,
    querySkill: FIXED_QUERY_SKILL,
    ingestSkill: FIXED_INGEST_SKILL,
    okfScript: FIXED_OKF_SCRIPT,
  };
}
