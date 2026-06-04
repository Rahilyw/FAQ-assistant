"""
Invoke the local MCP server (streamable-http) and call `search_faq`.

Usage:
    python invoke_mcp.py "how do i track my order?"

This script uses the `mcp` Python client to initialize a session and call the
`search_faq` tool, printing the JSON response.
"""

import os
import sys
import json
from pathlib import Path


def load_dotenvs():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    here = Path(__file__).parent
    for p in [here / ".env", here.parent / ".env", here.parent / "AgentRAG" / ".env"]:
        if p.exists():
            load_dotenv(p, override=False)


def main():
    load_dotenvs()
    question = sys.argv[1] if len(sys.argv) > 1 else "how do i track my order?"
    mcp_url = os.environ.get("MCP_URL", os.environ.get("MCP_TUNNEL_URL", "http://localhost:8000/mcp"))

    # First try a simple stateless HTTP POST (works for stateless servers).
    try:
        import httpx
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        call_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "search_faq",
            "params": {"user_question": question},
        }
        r = httpx.post(mcp_url, json=call_payload, headers=headers, timeout=60.0)
        r.raise_for_status()
        try:
            print(json.dumps(r.json(), indent=2, default=str))
        except Exception:
            print(r.text)
        return
    except Exception:
        pass

    import anyio
    from mcp.client.streamable_http import streamable_http_client
    from mcp.types import JSONRPCRequest, JSONRPCMessage
    from mcp.shared.message import SessionMessage

    async def _run():
        async with streamable_http_client(mcp_url) as (read_stream, write_stream, get_session_id):
            init_req = JSONRPCRequest.model_validate({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "invoke_mcp.py", "version": "1"},
                },
            })
            init_msg = JSONRPCMessage.model_validate(init_req.model_dump())
            await write_stream.send(SessionMessage(init_msg))

            init_resp = await read_stream.receive()
            if isinstance(init_resp, Exception):
                raise init_resp
            print("Initialize response:")
            print(json.dumps(init_resp.message.model_dump(), indent=2, default=str))

            call_req = JSONRPCRequest.model_validate({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "search_faq",
                "params": {"user_question": question},
            })
            call_msg = JSONRPCMessage.model_validate(call_req.model_dump())
            await write_stream.send(SessionMessage(call_msg))

            call_resp = await read_stream.receive()
            if isinstance(call_resp, Exception):
                raise call_resp
            print("\nsearch_faq response:")
            print(json.dumps(call_resp.message.model_dump(), indent=2, default=str))

    try:
        anyio.run(_run)
    except Exception:
        import httpx
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        try:
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "invoke_mcp.py", "version": "1"},
                },
            }
            r = httpx.post(mcp_url, json=init_payload, headers=headers, timeout=30.0)
            r.raise_for_status()
            print("Initialize response (stateless POST):")
            try:
                print(json.dumps(r.json(), indent=2, default=str))
            except Exception:
                print(r.text)

            call_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "search_faq",
                "params": {"user_question": question},
            }
            r2 = httpx.post(mcp_url, json=call_payload, headers=headers, timeout=60.0)
            r2.raise_for_status()
            print("\nsearch_faq response (stateless POST):")
            try:
                print(json.dumps(r2.json(), indent=2, default=str))
            except Exception:
                print(r2.text)
        except Exception as ex:
            print(json.dumps({"error": str(ex)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
