import logging
logger = logging.getLogger(__name__)
# app/services/openserp_manager.py
"""
ظ…ط¯ظٹط± ط­ط§ظˆظٹط© OpenSERP - ظ†ظ…ط· "ط§ظ„ظ…ظˆط±ط¯ ط¹ظ†ط¯ ط§ظ„ط·ظ„ط¨".

- ظ„ط§ ظ…ط±ط§ظ‚ط¨ ط¯ظˆط±ظٹ ظپظٹ ط§ظ„ط®ظ„ظپظٹط©.
- طھط´ط؛ظٹظ„ طھظ„ظ‚ط§ط¦ظٹ ط¹ظ†ط¯ ط¨ط¯ط، ط§ظ„ط¨ط­ط« (ط¥ط°ط§ ظ„ظ… ظٹظƒظ† ظٹط¹ظ…ظ„).
- ط¥ظٹظ‚ط§ظپ طھظ„ظ‚ط§ط¦ظٹ ط¹ظ†ط¯ ط§ظ†طھظ‡ط§ط، ط¢ط®ط± ط¨ط­ط« ظ†ط´ط·.
"""

import subprocess
import asyncio
import httpx
import logging
logger = logging.getLogger(__name__)



CONTAINER_NAME = "openserp"
OPENSERP_URL = "http://127.0.0.1:7000"
DOCKER_IMAGE = "karust/openserp:latest"

# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# ط¹ط¯ط§ط¯ ط§ظ„ط¨ط­ظˆط« ط§ظ„ظ†ط´ط·ط© + ظ‚ظپظ„
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
_active_searches: int = 0
_lock = asyncio.Lock()


def _run_docker(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    """طھط´ط؛ظٹظ„ ط£ظ…ط± docker ط¨ط£ظ…ط§ظ†."""
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "ط§ظ†طھظ‡طھ ط§ظ„ظ…ظ‡ظ„ط© (Docker ظ„ظ… ظٹط³طھط¬ط¨)"
    except FileNotFoundError:
        return False, "Docker ط؛ظٹط± ظ…ط«ط¨طھ ط£ظˆ ط؛ظٹط± ظ…طھط§ط­ ظپظٹ PATH"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def get_status() -> dict:
    """ط­ط§ظ„ط© ط§ظ„ط­ط§ظˆظٹط© + ظپط­طµ ط§ظ„طµط­ط©."""
    ok, output = _run_docker(
        [
            "ps",
            "-a",
            "--filter",
            f"name=^{CONTAINER_NAME}$",
            "--format",
            "{{.Status}}",
        ]
    )

    if not ok:
        return {
            "exists": False,
            "running": False,
            "healthy": False,
            "status": "docker_error",
            "message": output[:200],
            "active_searches": _active_searches,
        }

    if not output.strip():
        return {
            "exists": False,
            "running": False,
            "healthy": False,
            "status": "not_created",
            "message": "ط§ظ„ط­ط§ظˆظٹط© ط؛ظٹط± ظ…ظˆط¬ظˆط¯ط©",
            "active_searches": _active_searches,
        }

    container_status = output.strip()
    running = container_status.lower().startswith("up")

    healthy = False
    if running:
        try:
            with httpx.Client(timeout=3) as client:
                r = client.get(f"{OPENSERP_URL}/health")
                healthy = r.status_code == 200
        except Exception:
            healthy = False

    return {
        "exists": True,
        "running": running,
        "healthy": healthy,
        "status": container_status,
        "message": (
            "ظٹط¹ظ…ظ„ ط¨ط´ظƒظ„ ط³ظ„ظٹظ…"
            if healthy
            else ("ظٹط¹ظ…ظ„ ظ„ظƒظ† ط؛ظٹط± ظ…ط³طھط¬ظٹط¨" if running else "ظ…طھظˆظ‚ظپ")
        ),
        "active_searches": _active_searches,
    }


def start() -> dict:
    """طھط´ط؛ظٹظ„ ط§ظ„ط­ط§ظˆظٹط© (ط£ظˆ ط¥ظ†ط´ط§ط¤ظ‡ط§ ط¥ظ† ظ„ظ… طھظƒظ† ظ…ظˆط¬ظˆط¯ط©)."""
    status = get_status()

    if status.get("running"):
        return {"success": True, "message": "OpenSERP ظٹط¹ظ…ظ„ ط¨ط§ظ„ظپط¹ظ„", "status": status}

    if status.get("exists"):
        logger.info("â–¶ï¸ڈ طھط´ط؛ظٹظ„ OpenSERP (ط§ظ„ط­ط§ظˆظٹط© ظ…ظˆط¬ظˆط¯ط©)")
        ok, output = _run_docker(["start", CONTAINER_NAME])
        return {"success": ok, "message": output, "status": get_status()}

    logger.info("ًں†• ط¥ظ†ط´ط§ط، ظˆطھط´ط؛ظٹظ„ OpenSERP")
    ok, output = _run_docker(
        [
            "run",
            "-d",
            "--name",
            CONTAINER_NAME,
            "-p",
            "127.0.0.1:7000:7000",
            "--restart",
            "no",  # â†گ ظ„ط§ ط¥ط¹ط§ط¯ط© طھط´ط؛ظٹظ„ طھظ„ظ‚ط§ط¦ظٹط©
            DOCKER_IMAGE,
            "serve",
            "-a",
            "0.0.0.0",
            "-p",
            "7000",
        ]
    )
    return {"success": ok, "message": output, "status": get_status()}


def stop() -> dict:
    """ط¥ظٹظ‚ط§ظپ ط§ظ„ط­ط§ظˆظٹط© (ط¨ط¯ظˆظ† ط­ط°ظپظ‡ط§)."""
    status = get_status()
    if not status.get("running"):
        return {"success": True, "message": "OpenSERP ظ…طھظˆظ‚ظپ ط¨ط§ظ„ظپط¹ظ„", "status": status}

    logger.info("âڈ¸ï¸ڈ ط¥ظٹظ‚ط§ظپ OpenSERP")
    ok, output = _run_docker(["stop", CONTAINER_NAME], timeout=30)
    return {"success": ok, "message": output, "status": get_status()}


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# ط§ظ„طھط´ط؛ظٹظ„ ط¹ظ†ط¯ ط§ظ„ط­ط§ط¬ط© (ظ„ط§ ظٹظˆط¬ط¯ ظ…ط±ط§ظ‚ط¨ ط¯ظˆط±ظٹ)
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
async def _ensure_ready(max_wait: int = 30) -> dict:
    """ظٹطھط£ظƒط¯ ط£ظ† OpenSERP ط¬ط§ظ‡ط². ظٹط´ط؛ظ‘ظ„ظ‡ ط¥ظ† ظ„ظ… ظٹظƒظ†."""
    status = get_status()
    if status.get("healthy"):
        return {"ready": True, "status": status}

    logger.info("ًںڑ€ طھط´ط؛ظٹظ„ OpenSERP ظ„ظ„ط¨ط­ط«...")
    result = start()

    if not result.get("success"):
        logger.error(f"â‌Œ ظپط´ظ„ ط§ظ„طھط´ط؛ظٹظ„: {result.get('message')}")
        return {"ready": False, "error": result.get("message"), "status": get_status()}

    for i in range(max_wait):
        await asyncio.sleep(1)
        status = get_status()
        if status.get("healthy"):
            logger.info(f"âœ… OpenSERP ط¬ط§ظ‡ط² ط¨ط¹ط¯ {i+1} ط«ط§ظ†ظٹط©")
            return {"ready": True, "status": status}

    logger.error(f"â‌Œ OpenSERP ظ„ظ… ظٹطµط¨ط­ ط¬ط§ظ‡ط²ظ‹ط§ ط®ظ„ط§ظ„ {max_wait} ط«ط§ظ†ظٹط©")
    return {"ready": False, "error": "ظ„ظ… ظٹطµط¨ط­ ط¬ط§ظ‡ط²ظ‹ط§", "status": get_status()}


# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# ط¯ظˆط±ط© ط­ظٹط§ط© ط§ظ„ط¨ط­ط«: acquire / release
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
async def acquire_for_search() -> dict:
    """
    - ظٹط²ظٹط¯ ط¹ط¯ط§ط¯ ط§ظ„ط¨ط­ظˆط« ط§ظ„ظ†ط´ط·ط©.
    - ط¥ط°ط§ ظƒط§ظ† ط£ظˆظ„ ط¨ط­ط«طŒ ظٹط´ط؛ظ‘ظ„ OpenSERP ظˆظٹظ†طھط¸ط±ظ‡.
    - ط¥ط°ط§ ظƒط§ظ† ظ‡ظ†ط§ظƒ ط¨ط­ط« ظ†ط´ط· ط¨ط§ظ„ظپط¹ظ„طŒ ظ„ط§ ظٹظپط¹ظ„ ط´ظٹط¦ظ‹ط§ (ط³ط±ظٹط¹).
    """
    global _active_searches

    async with _lock:
        _active_searches += 1
        is_first = _active_searches == 1
        current_count = _active_searches

    logger.info(f"ًں“ٹ acquire_for_search: active={current_count}, is_first={is_first}")

    if not is_first:
        # ط¨ط­ط« ط¢ط®ط± ظٹط¹ظ…ظ„ ط¨ط§ظ„ظپط¹ظ„ â†’ ظ„ط§ ط­ط§ط¬ط© ظ„طھط´ط؛ظٹظ„ ط´ظٹط،
        return {"ready": True, "already_running": True, "status": get_status()}

    # ط£ظˆظ„ ط¨ط­ط« â†’ ط´ط؛ظ‘ظ„ OpenSERP
    return await _ensure_ready()


async def release_after_search() -> dict:
    """
    - ظٹظ‚ظ„ظ„ ط¹ط¯ط§ط¯ ط§ظ„ط¨ط­ظˆط« ط§ظ„ظ†ط´ط·ط©.
    - ط¥ط°ط§ ظƒط§ظ† ط¢ط®ط± ط¨ط­ط«طŒ ظٹظˆظ‚ظپ OpenSERP.
    """
    global _active_searches

    async with _lock:
        _active_searches = max(0, _active_searches - 1)
        is_last = _active_searches == 0
        current_count = _active_searches

    logger.info(f"ًں“ٹ release_after_search: active={current_count}, is_last={is_last}")

    if not is_last:
        # ظ‡ظ†ط§ظƒ ط¨ط­ط« ط¢ط®ط± ظٹط¹ظ…ظ„ â†’ ظ„ط§ طھظˆظ‚ظپ
        return {"stopped": False, "reason": "ط¨ط­ظˆط« ط£ط®ط±ظ‰ ظ†ط´ط·ط©", "status": get_status()}

    # ط¢ط®ط± ط¨ط­ط« â†’ ط£ظˆظ‚ظپ
    logger.info("ًں›‘ ط¥ظٹظ‚ط§ظپ OpenSERP (ط§ظƒطھظ…ظ„طھ ط¬ظ…ظٹط¹ ط§ظ„ط¨ط­ظˆط« ط§ظ„ظ†ط´ط·ط©)")
    result = stop()
    return {"stopped": True, "result": result, "status": get_status()}

