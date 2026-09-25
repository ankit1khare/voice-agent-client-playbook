"""Measure ready-text to first client PCM, with cold and warm runs separated."""

import argparse
import asyncio
import json
import math
import os
import statistics
import time
import wave
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp
from dotenv import load_dotenv
from livekit.agents import APIConnectOptions
from livekit.plugins import rime

from nudge_voice_agent.settings import CODA_WEBSOCKET_URL, DEFAULT_TTS_VOICE

TEXTS = [
    "I can help you find the right place to upload your documents.",
    "Of course. What date would you like to request for the extension?",
    "Your request still needs review. It has not been approved yet.",
    "Take your time. Let me know when you can see Business Documents.",
    "Thanks for letting me know. Is there anything else I can help with?",
]
CONNECT = APIConnectOptions(max_retry=0, timeout=20.0)


async def sample(speech: rime.TTS, text: str, path: Path) -> dict[str, Any]:
    stream = speech.stream(conn_options=CONNECT)
    pcm = bytearray()
    first = None
    ids: set[str] = set()
    started = time.perf_counter()
    try:
        stream.push_text(text)
        stream.end_input()
        async with asyncio.timeout(30):
            async for event in stream:
                if first is None:
                    first = time.perf_counter() - started
                pcm.extend(event.frame.data)
                ids.add(event.request_id)
        if first is None or not pcm:
            raise RuntimeError("No audio returned")
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(speech.sample_rate)
            wav.writeframes(pcm)
        return {
            "status": "ok",
            "first_pcm_ms": first * 1000,
            "audio_duration_seconds": len(pcm) / (2 * speech.sample_rate),
            "provider_request_count": len(ids),
            "audio_file": path.name,
        }
    except Exception as error:
        return {"status": "error", "error_type": type(error).__name__}
    finally:
        await stream.aclose()


async def run(output: Path, count: int) -> None:
    output.mkdir(parents=True, exist_ok=False)
    result: dict[str, Any] = {
        "started_at": datetime.now(UTC).isoformat(),
        "endpoint": CODA_WEBSOCKET_URL,
        "voice": DEFAULT_TTS_VOICE,
        "client": "Local Mac, America/Los_Angeles; no VPN or routing assumption",
        "sample_rate": 24000,
        "concurrency": 1,
        "warm_attempts_planned": count,
        "timing_scope": (
            "Complete text pushed into LiveKit Rime plugin to first PCM frame "
            "received by client"
        ),
        "limitations": (
            "Includes client/provider/network work. Excludes STT, LLM generation, "
            "telephony and audible playback. Sequential synthetic requests, not "
            "a load test or competitor comparison. One cold sample is not a "
            "cold-start distribution."
        ),
        "percentile_method": "P50 median; P95 nearest rank, ceil(0.95*n)",
        "runs": [],
    }
    async with aiohttp.ClientSession() as http:
        speech = rime.TTS(
            websocket_url=CODA_WEBSOCKET_URL,
            speaker=DEFAULT_TTS_VOICE,
            lang="en",
            api_key=os.environ["RIME_API_KEY"],
            http_session=http,
        )
        try:
            for i in range(count + 1):
                condition = "cold" if i == 0 else "warm"
                text = TEXTS[(i - 1) % len(TEXTS)] if i else TEXTS[0]
                item = await sample(speech, text, output / f"{condition}-{i:02}.wav")
                item.update(condition=condition, index=i, text=text)
                result["runs"].append(item)
                (output / "results.json").write_text(
                    json.dumps(result, indent=2) + "\n"
                )
                print(json.dumps(item), flush=True)
                if i == 0 and item["status"] != "ok":
                    raise RuntimeError(
                        "Cold request failed; do not label later requests warm"
                    )
        finally:
            await speech.aclose()
    warm = [x for x in result["runs"] if x["condition"] == "warm"]
    times = sorted(x["first_pcm_ms"] for x in warm if x["status"] == "ok")
    result["warm_summary"] = {
        "attempts": len(warm),
        "successful": len(times),
        "failures": len(warm) - len(times),
        "p50_ms": statistics.median(times) if times else None,
        "p95_ms": times[math.ceil(0.95 * len(times)) - 1] if times else None,
        "min_ms": min(times) if times else None,
        "max_ms": max(times) if times else None,
    }
    result["completed_at"] = datetime.now(UTC).isoformat()
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["warm_summary"]), flush=True)


if __name__ == "__main__":
    load_dotenv(".env.local")
    load_dotenv(".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    asyncio.run(run(args.output, args.count))
