# Video Test - Channel Intro Battle (OpenMontage)

Create a **10-second animated intro video** for the YouTube channel **«Ботанутый Костя»** using **OpenMontage, which is installed on this computer** at:

`<your OpenMontage folder>`

## Workspace

- You are running inside the OpenMontage folder. Before doing anything else, read `AGENT_GUIDE.md` and follow its rules, pipelines, skills and tools. If your working directory is not `<your OpenMontage folder>`, stop and tell me.
- Use OpenMontage's own capabilities: its pipelines, director skills, tool registry, composition runtimes (Remotion / HyperFrames), audio tools and reviewer. Run the preflight and check which tools are actually available on this machine instead of assuming.
- Project ID: `intro-battle-{MODEL}`. All files and the final render go inside this project's workspace.

## The brief

- Channel: **«Ботанутый Костя»** (exact Cyrillic spelling). A Russian-speaking YouTube channel about AI models, vibe coding and automation. The host tests new neural networks, builds apps with them and compares them. Tone: smart, nerdy, playful, self-ironic, energetic.
- Duration: **exactly 10 seconds**. Format: **1920x1080, 30 fps, MP4 with sound**.
- The channel name must be clearly readable on screen for at least the final 1.5 seconds and must be spelled exactly «Ботанутый Костя».
- Sound design and/or music must be synced to the motion.
- Voice-over is optional: use it only if it makes the intro better.
- It will be played at the start of every video, so it must be memorable and rewatchable. **A concept, not just flying text.** Surprise me.

## Rules

- **Tools:** paid generation goes **only through kie.ai**, using the OpenMontage tools `kie_image` (images, GPT Image 2.5 Flare), `kie_video` (Kling 3.0 / Hailuo / Veo 3.1 clips), `kie_music` (Suno music) and `kie_tts` (ElevenLabs voice). The key is already configured in `.env`. Do not use any other paid provider. Free and local tools (composition runtimes, FFmpeg, local audio) are allowed without limits.
- **Budget:** maximum **$1** of kie.ai spend for this whole run. This is a hard limit and it is also enforced by the tools: each kie tool refuses a call that would exceed the limit and reports `budget_remaining_usd` after every call. Plan the paid calls to fit, prefer cheaper models and short clips, announce each paid call (tool, model, estimated cost) before making it, but do not wait for my reply.
- **Approvals:** I explicitly pre-authorize the full run. All approval gates are approved in advance, including the proposal, the composition runtime choice (present both runtimes briefly in your plan, then choose yourself), the music plan, the assets review, paid kie.ai calls within the budget, and any fallback that stays within kie.ai and local tools. Record this pre-authorization as an `approval_policy` entry in the `decision_log`, then work autonomously from idea to final render without waiting for me.
- **Quality check:** before finishing, render the final video, check frames from the beginning, middle and end, confirm the duration, resolution, audio track and the spelling of the channel name, and fix anything wrong.

## Finish

When done, reply with:

1. The exact path to the final MP4.
2. One paragraph describing the concept.
3. The pipeline, runtime and main tools you used.
4. Total kie.ai spend for this run (from `projects/intro-battle-{MODEL}/kie_spend.json`).

Do not ask questions. Make all creative and technical decisions yourself.
