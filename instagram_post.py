"""
instagram_post.py
Publishes a finished Reel to an Instagram Business/Creator account via the
Meta Graph API (Content Publishing).

ONE-TIME SETUP (free, done by you in the Meta Developer console — see
README.md "Instagram Setup" section for the click-by-click version):
  1. Instagram account converted to a Business or Creator account, linked
     to a Facebook Page.
  2. A Meta App created at developers.facebook.com, with the
     "instagram_content_publish" permission.
  3. A long-lived access token + your Instagram Business Account ID.
  4. Public App Review approval if you want this to run with nobody
     clicking "confirm" — Meta requires review before a non-tester app
     can publish automatically. Free, but budget a few days for it.

Until App Review is approved, this still works for your OWN account if
it's added as a Tester/Admin/Developer on the Meta App (development mode).

Env vars expected (see .env.example):
    IG_ACCESS_TOKEN
    IG_BUSINESS_ACCOUNT_ID
"""
from __future__ import annotations
import os
import time
import requests

GRAPH_VERSION = "v21.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


def publish_reel(video_public_url: str, caption: str) -> str:
    """video_public_url must be a URL Meta's servers can fetch (e.g. a link
    to the file in a public S3/Cloudflare R2 bucket, or a GitHub Release
    asset URL) — Graph API does not accept raw file uploads for Reels.
    Returns the published media ID."""
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]

    # Step 1: create a media container
    create = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_public_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    create.raise_for_status()
    creation_id = create.json()["id"]

    # Step 2: poll until the container finishes processing
    status_url = f"{GRAPH_URL}/{creation_id}"
    for _ in range(30):
        r = requests.get(status_url, params={"fields": "status_code", "access_token": token}, timeout=30)
        r.raise_for_status()
        status = r.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Instagram container {creation_id} failed processing")
        time.sleep(10)
    else:
        raise TimeoutError(f"Instagram container {creation_id} did not finish in time")

    # Step 3: publish it
    publish = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    publish.raise_for_status()
    return publish.json()["id"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: python instagram_post.py <public_video_url> <caption_text>")
        raise SystemExit(1)
    media_id = publish_reel(sys.argv[1], sys.argv[2])
    print(f"Published. Media ID: {media_id}")
