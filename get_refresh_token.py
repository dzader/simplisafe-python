#!/usr/bin/env python3
"""
Script to obtain a SimpliSafe refresh token for testing.

This script will walk you through the authentication process and
give you a refresh token that you can use for testing camera streaming.
"""

import asyncio
import sys
import webbrowser
from aiohttp import ClientSession
from simplipy import API
from simplipy.util.auth import (
    get_auth0_code_challenge,
    get_auth0_code_verifier,
    get_auth_url,
)


async def get_refresh_token():
    """Get a refresh token for SimpliSafe API access."""

    print("SimpliSafe Refresh Token Setup")
    print("=" * 35)
    print()
    print("This script will help you get a refresh token that you can")
    print("use for testing camera streaming functionality.")
    print()

    # Generate OAuth2 parameters
    code_verifier = get_auth0_code_verifier()
    code_challenge = get_auth0_code_challenge(code_verifier)
    auth_url = get_auth_url(code_challenge)

    print("Step 1: Open SimpliSafe login page")
    print("-" * 35)
    try:
        input("Press <ENTER> to open the SimpliSafe login page in your browser... ")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return None

    webbrowser.open(auth_url)

    print("\nStep 2: Complete authentication")
    print("-" * 35)
    print("1. Log in to your SimpliSafe account")
    print("2. Copy the authorization code from the URL or page")
    print("3. Paste it below")
    print()

    try:
        auth_code = input("Enter the authorization code: ").strip()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return None

    if not auth_code:
        print("No authorization code entered.")
        return None

    print("\nStep 3: Getting refresh token...")
    print("-" * 35)

    async with ClientSession() as session:
        try:
            # Authenticate and get refresh token
            api = await API.async_from_auth(
                auth_code,
                code_verifier,
                session=session,
            )

            refresh_token = api.refresh_token

            if refresh_token:
                print("✅ Success! Here's your refresh token:")
                print()
                print("=" * 60)
                print(f"REFRESH_TOKEN={refresh_token}")
                print("=" * 60)
                print()
                print("Save this token - you can use it for testing!")
                print()
                print("Usage examples:")
                print(f'export SIMPLISAFE_REFRESH_TOKEN="{refresh_token}"')
                print("python3 save_camera_stream.py")
                print()
                print("Or in your Python code:")
                print(f'api = await API.async_from_refresh_token("{refresh_token}", session=session)')

                return refresh_token
            else:
                print("❌ Failed to get refresh token")
                return None

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print()
            print("Common issues:")
            print("- Authorization code already used (try getting a new one)")
            print("- Authorization code expired (they expire quickly)")
            print("- Invalid credentials")
            print("- Network connectivity issues")
            return None


async def main():
    """Main entry point."""
    refresh_token = await get_refresh_token()

    if refresh_token:
        print("\n🎉 Setup complete!")
        print("\nYou can now test camera streaming with:")
        print("python3 test_camera_functionality.py")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
