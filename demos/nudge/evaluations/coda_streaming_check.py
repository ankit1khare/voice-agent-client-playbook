"""Check real Coda streaming with controlled text arrival and cancellation.

This is a client-side experiment, not a phone latency or voice-quality benchmark.
Uses one endpoint, voice, text, and scheduled input rate for both conditions.
"""

import argparse
import asyncio
import json
import os
import statistics
import time
import wave
from pathlib import Path
from typing import NotRequired, TypedDict

import aiohttp
from dotenv import load_dotenv
from livekit.agents import APIConnectOptions
from livekit.plugins import rime

from nudge_voice_agent.settings import CODA_WEBSOCKET_URL, DEFAULT_TTS_VOICE

TEXT = (
    "I can help with your documents. "
    "You can find the upload page under Settings, then Business Documents. "
    "If you need more time, tell me the date you have in mind. "
    "Any extension request will still need review. "
)
CHUNKS = [word + " " for word in TEXT.split()]
INTERVAL_SECONDS = 0.08
CONNECT = APIConnectOptions(max_retry=0, timeout=20.0)


class TimingRun(TypedDict):
    mode: str
    first_pcm_seconds: float
    all_text_available_seconds: float
    audio_before_all_text: bool
    audio_duration_seconds: float
    provider_request_count: int
    audio_file: str
    pair: NotRequired[int]


async def measure(speech: rime.TTS, mode: str, output: Path) -> TimingRun:
    """Compare streaming vs holding identical scheduled text until it is complete."""
    stream = speech.stream(conn_options=CONNECT)
    started = time.perf_counter()
    first_audio: float | None = None
    input_finished = 0.0
    pcm = bytearray()
    request_ids: set[str] = set()

    async def send() -> None:
        nonlocal input_finished
        for i, chunk in enumerate(CHUNKS):
            await asyncio.sleep(
                max(0.0, started + i * INTERVAL_SECONDS - time.perf_counter())
            )
            if mode == "streamed":
                stream.push_text(chunk)
        input_finished = time.perf_counter() - started
        if mode == "buffered":
            stream.push_text("".join(CHUNKS))
        stream.end_input()

    sender = asyncio.create_task(send())
    try:
        async with asyncio.timeout(45):
            async for event in stream:
                if first_audio is None:
                    first_audio = time.perf_counter() - started
                pcm.extend(event.frame.data)
                request_ids.add(event.request_id)
            await sender
        if not pcm or first_audio is None:
            raise RuntimeError("Coda returned no audio")
        with wave.open(str(output), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(speech.sample_rate)
            wav.writeframes(pcm)
        return {
            "mode": mode,
            "first_pcm_seconds": first_audio,
            "all_text_available_seconds": input_finished,
            "audio_before_all_text": first_audio < input_finished,
            "audio_duration_seconds": len(pcm) / (2 * speech.sample_rate),
            "provider_request_count": len(request_ids),
            "audio_file": output.name,
        }
    finally:
        sender.cancel()
        await asyncio.gather(sender, return_exceptions=True)
        await stream.aclose()


async def cancel_then_speak(speech: rime.TTS) -> dict[str, object]:
    """Cancel with input still open, then verify a subsequent turn produces audio."""
    first = speech.stream(conn_options=CONNECT)
    try:
        first.push_text(
            "This sentence is being interrupted. Here is more information. "
        )
        async with asyncio.timeout(30):
            await anext(first)
        started = time.perf_counter()
        async with asyncio.timeout(10):
            await first.aclose()
        close_seconds = time.perf_counter() - started
    finally:
        await first.aclose()

    following = speech.stream(conn_options=CONNECT)
    frames = 0
    try:
        following.push_text("The next reply is ready. Your request still needs review.")
        following.end_input()
        async with asyncio.timeout(30):
            async for event in following:
                frames += event.frame.samples_per_channel
        if frames == 0:
            raise RuntimeError("The turn after cancellation produced no audio")
        return {
            "passed": True,
            "cancel_close_seconds": close_seconds,
            "next_turn_samples": frames,
        }
    finally:
        await following.aclose()


async def run(output: Path) -> None:
    """Run counterbalanced pairs after a warmup; retain every successful sample."""
    output.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as http:
        speech = rime.TTS(
            websocket_url=CODA_WEBSOCKET_URL,
            speaker=DEFAULT_TTS_VOICE,
            lang="en",
            api_key=os.environ["RIME_API_KEY"],
            http_session=http,
        )
        try:
            warmup = speech.stream(conn_options=CONNECT)
            try:
                warmup.push_text("Nudge is ready for a call.")
                warmup.end_input()
                async with asyncio.timeout(30):
                    async for _ in warmup:
                        pass
            finally:
                await warmup.aclose()
            runs = []
            for pair in range(3):
                order = (
                    ("streamed", "buffered")
                    if pair % 2 == 0
                    else ("buffered", "streamed")
                )
                for mode in order:
                    item = await measure(
                        speech, mode, output / f"pair-{pair + 1}-{mode}.wav"
                    )
                    item["pair"] = pair + 1
                    runs.append(item)
                    print(json.dumps(item), flush=True)
            cancellation = await cancel_then_speak(speech)
            result = {
                "endpoint": CODA_WEBSOCKET_URL,
                "voice": DEFAULT_TTS_VOICE,
                "sample_rate": speech.sample_rate,
                "input_text": TEXT,
                "input_interval_seconds": INTERVAL_SECONDS,
                "input_chunks": len(CHUNKS),
                "pairs": 3,
                "timing_scope": (
                    "first scheduled text chunk to first received PCM; warm connection"
                ),
                "limitations": (
                    "Synthetic text schedule; no LLM, STT, room, PSTN, or speaker "
                    "playback. Same new Coda endpoint in both conditions, "
                    "not a legacy API comparison. No prosody score."
                ),
                "runs": runs,
                "median_first_pcm_seconds": {
                    mode: statistics.median(
                        x["first_pcm_seconds"] for x in runs if x["mode"] == mode
                    )
                    for mode in ("streamed", "buffered")
                },
                "cancellation": cancellation,
            }
            (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "medians": result["median_first_pcm_seconds"],
                        "cancellation": cancellation,
                    }
                ),
                flush=True,
            )
        finally:
            await speech.aclose()


if __name__ == "__main__":
    load_dotenv(".env.local")
    load_dotenv(".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.output))
