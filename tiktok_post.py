"""
tiktok_post.py
Publishes a finished video to TikTok via the Content Posting API
(Direct Post, PULL_FROM_URL variant).

IMPORTANT — read before assuming this posts fully automatically:
  * A brand-new TikTok Developer app is "unaudited". Unaudited apps can
    only post as SELF_ONLY (private, visible only to you) and are capped
    at 5 distinct creators/24h. This is fine for testing, not for growth.
  * To post publicly, you must submit your app for TikTok's free
    "Direct Post" audit (see README.md "TikTok Setup"). Budget some days
    for review, and expect to demo a simple confirmation step in your
    own flow before a post is finalized — TikTok's guidelines require
    the creator to knowingly approve what gets posted, which most
    scheduling tools (Buffer, Later, Metricool, etc.) satisfy once when
    you approve a batch, not on every single publish.
  * MEDIA_UPLOAD mode (no audit needed) instead sends the video as a
    draft to your TikTok inbox for a one-tap manual publish — a solid
    zero-setup fallback while your audit is pending.

Env vars expected (see .env.example):
    TIKTOK_ACCESS_TOKEN
"""
from __future__ import annotations
import os
import requests

BASE_URL = "https://open.tiktokapis.com/v2"


def post_direct(video_public_url: str, title: str, privacy_level: str = "SELF_ONLY") -> dict:
    """privacy_level: SELF_ONLY until your app passes the Direct Post audit,
    then e.g. PUBLIC_TO_EVERYONE. video_public_url must be a URL TikTok's
    servers can fetch (see instagram_post.py docstring — same constraint)."""
    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    resp = requests.post(
        f"{BASE_URL}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_public_url,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def post_to_inbox_draft(video_public_url: str) -> dict:
    """No-audit-required fallback: sends the video to the creator's TikTok
    inbox as a draft they finish publishing with one tap in the app."""
    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    resp = requests.post(
        f"{BASE_URL}/post/publish/inbox/video/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"source_info": {"source": "PULL_FROM_URL", "video_url": video_public_url}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: python tiktok_post.py <public_video_url> <title>")
        raise SystemExit(1)
    result = post_to_inbox_draft(sys.argv[1])
    print(result)
