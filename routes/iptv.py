from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["iptv"])

# --- IPTV ---
@router.get("/iptv/channels")
def get_iptv_channels(token: str = Header(None)):
    iptv_data = get_test_data("iptv", {})
    return {"channels": iptv_data.get("channels", [])}


@router.get("/iptv/playlists")
def get_iptv_playlists(token: str = Header(None)):
    iptv_data = get_test_data("iptv", {})
    return {"playlists": iptv_data.get("playlists", [])}


@router.get("/iptv/time")
def get_iptv_time(token: str = Header(None)):
    """Get IPTV current time"""
    iptv_data = get_test_data("iptv", {})
    return iptv_data.get("time", {})


@router.get("/iptv/program/{channel_id}/{time}")
def get_iptv_program(channel_id: str, time: str, full: bool = Query(False), token: str = Header(None)):
    """Get IPTV program for channel and time"""
    key = f"{channel_id}_{time}"
    iptv_data = get_test_data("iptv", {})
    program = iptv_data.get("program", {})
    if key not in program:
        program[key] = {
            "channel_id": channel_id,
            "time": int(time),
            "programs": [
                {"title": f"Program {channel_id}-1", "start": int(time), "end": int(time) + 3600},
                {"title": f"Program {channel_id}-2", "start": int(time) + 3600, "end": int(time) + 7200}
            ]
        }
        iptv_data["program"] = program
        update_test_data("iptv", iptv_data)
    return program[key] 