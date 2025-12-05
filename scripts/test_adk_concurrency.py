#!/usr/bin/env python3
"""
Script to test ADK API concurrency by:
1. Creating 10 sessions
2. Sending 10 "hi" messages to each session
3. Sending "try level 1" message to each session

Usage:
    uv run scripts/test_adk_concurrency.py
    # Or with custom ADK API URL:
    ADK_API_URL=http://localhost:8000 uv run scripts/test_adk_concurrency.py
"""

import asyncio
import os
import time
from typing import List, Tuple

import httpx


# Configuration
ADK_API_URL = os.getenv("ADK_API_URL", "http://127.0.0.1:8000")
APP_NAME = "sub_agents"
NUM_SESSIONS = 10
NUM_HI_MESSAGES = 10


async def create_session(
    client: httpx.AsyncClient, user_id: str, session_id: str
) -> Tuple[bool, str]:
    """Create a session in the ADK API"""
    try:
        response = await client.post(
            f"{ADK_API_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            json=None,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return True, f"Session {session_id} created"
    except httpx.HTTPStatusError as e:
        return (
            False,
            f"Failed to create session {session_id}: {e.response.status_code} - {e.response.text}",
        )
    except Exception as e:
        return False, f"Error creating session {session_id}: {str(e)}"


async def send_message(
    client: httpx.AsyncClient, user_id: str, session_id: str, message: str
) -> Tuple[bool, str, dict]:
    """Send a message to the ADK API"""
    payload = {
        "appName": APP_NAME,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {"role": "user", "parts": [{"text": message}]},
        "streaming": False,
    }

    try:
        response = await client.post(
            f"{ADK_API_URL}/run",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60.0,
        )
        response.raise_for_status()
        return True, f"Message sent to {session_id}", response.json()
    except httpx.HTTPStatusError as e:
        return (
            False,
            f"HTTP error sending message to {session_id}: {e.response.status_code} - {e.response.text}",
            {},
        )
    except httpx.TimeoutException:
        return False, f"Timeout sending message to {session_id}", {}
    except Exception as e:
        return False, f"Error sending message to {session_id}: {str(e)}", {}


async def test_session(session_num: int) -> dict:
    """Test a single session: create it, send hi messages, then send level 1 message"""
    user_id = f"test_user_{session_num}"
    session_id = f"test_session_{session_num}"

    results = {
        "session_id": session_id,
        "user_id": user_id,
        "session_created": False,
        "hi_messages": [],
        "level_message": None,
        "errors": [],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Create session
        success, message = await create_session(client, user_id, session_id)
        results["session_created"] = success
        if not success:
            results["errors"].append(message)
            return results

        # Step 2: Send 10 "hi" messages concurrently
        hi_tasks = [
            send_message(client, user_id, session_id, "hi")
            for _ in range(NUM_HI_MESSAGES)
        ]
        hi_results = await asyncio.gather(*hi_tasks, return_exceptions=True)

        for i, result in enumerate(hi_results):
            if isinstance(result, Exception):
                results["errors"].append(
                    f"Hi message {i+1} exception: {str(result)}"
                )
            else:
                success, msg, response_data = result
                results["hi_messages"].append(
                    {
                        "message_num": i + 1,
                        "success": success,
                        "message": msg,
                        "has_response": bool(response_data),
                    }
                )
                if not success:
                    results["errors"].append(msg)

        # Step 3: Send "try level 1" message
        success, msg, response_data = await send_message(
            client, user_id, session_id, "try level 1"
        )
        results["level_message"] = {
            "success": success,
            "message": msg,
            "has_response": bool(response_data),
        }
        if not success:
            results["errors"].append(msg)

    return results


async def main():
    """Main function to run concurrent ADK API tests"""
    print(f"🚀 Starting ADK API Concurrency Test")
    print(f"   ADK API URL: {ADK_API_URL}")
    print(f"   Number of sessions: {NUM_SESSIONS}")
    print(f"   Hi messages per session: {NUM_HI_MESSAGES}")
    print(f"   Total messages: {NUM_SESSIONS * (NUM_HI_MESSAGES + 1)}")
    print()

    start_time = time.time()

    # Create all sessions concurrently
    print("📝 Step 1: Creating sessions concurrently...")
    session_tasks = [test_session(i) for i in range(NUM_SESSIONS)]
    all_results = await asyncio.gather(*session_tasks, return_exceptions=True)

    end_time = time.time()
    elapsed = end_time - start_time

    # Process results
    successful_sessions = 0
    total_hi_messages = 0
    successful_hi_messages = 0
    successful_level_messages = 0
    total_errors = 0

    print("\n📊 Results:")
    print("=" * 80)

    for i, result in enumerate(all_results):
        if isinstance(result, Exception):
            print(f"❌ Session {i}: Exception - {str(result)}")
            total_errors += 1
            continue

        session_id = result["session_id"]
        session_ok = result["session_created"]
        hi_count = len([m for m in result["hi_messages"] if m["success"]])
        level_ok = (
            result["level_message"]["success"]
            if result["level_message"]
            else False
        )

        if session_ok and hi_count == NUM_HI_MESSAGES and level_ok:
            successful_sessions += 1
            status = "✅"
        else:
            status = "⚠️"

        print(
            f"{status} {session_id}: "
            f"Session={session_ok}, "
            f"Hi={hi_count}/{NUM_HI_MESSAGES}, "
            f"Level={level_ok}"
        )

        if result["errors"]:
            for error in result["errors"][:3]:  # Show first 3 errors
                print(f"   ⚠️  {error}")
            if len(result["errors"]) > 3:
                print(f"   ... and {len(result['errors']) - 3} more errors")

        total_hi_messages += len(result["hi_messages"])
        successful_hi_messages += hi_count
        if level_ok:
            successful_level_messages += 1

    print("=" * 80)
    print(f"\n📈 Summary:")
    print(f"   Total time: {elapsed:.2f} seconds")
    print(f"   Successful sessions: {successful_sessions}/{NUM_SESSIONS}")
    print(
        f"   Successful hi messages: {successful_hi_messages}/{total_hi_messages}"
    )
    print(
        f"   Successful level messages: {successful_level_messages}/{NUM_SESSIONS}"
    )
    print(f"   Total errors: {total_errors}")
    print(
        f"   Messages per second: {(total_hi_messages + NUM_SESSIONS) / elapsed:.2f}"
    )

    if successful_sessions == NUM_SESSIONS:
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠️  {NUM_SESSIONS - successful_sessions} sessions had issues")


if __name__ == "__main__":
    asyncio.run(main())
