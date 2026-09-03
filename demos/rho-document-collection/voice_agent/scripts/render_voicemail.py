"""Render the Rho demo voicemail clip with LiveKit Inference and Rime Coda."""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import inference, utils

COMPONENT_ROOT = Path(__file__).resolve().parent.parent
SOLUTION_ROOT = COMPONENT_ROOT.parent
SCRIPT_PATH = SOLUTION_ROOT / "assets" / "jenny_voicemail_reminder.txt"
OUTPUT_PATH = SOLUTION_ROOT / "assets" / "jenny_voicemail_reminder.wav"


async def render_voicemail() -> None:
    """Synthesize the approved voicemail script as a mono PCM WAV file."""
    load_dotenv(COMPONENT_ROOT / ".env.local")
    script = SCRIPT_PATH.read_text(encoding="utf-8").strip()

    async with utils.http_context.open():
        tts = inference.TTS(model="rime/coda", voice="wawona")
        try:
            frame = await tts.synthesize(script).collect()
        finally:
            await tts.aclose()

    OUTPUT_PATH.write_bytes(frame.to_wav_bytes())
    print(
        f"Rendered {OUTPUT_PATH} "
        f"({frame.duration:.2f}s, {frame.sample_rate}Hz, {frame.num_channels} channel)"
    )


def main() -> None:
    """Run the voicemail renderer."""
    asyncio.run(render_voicemail())


if __name__ == "__main__":
    main()
