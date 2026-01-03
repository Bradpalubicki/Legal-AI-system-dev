#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-Time Monitoring via WebSocket
Watch API calls, errors, and system health in real-time
"""

import asyncio
import websockets
import json
import sys
import io
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def monitor():
    """Connect to monitoring WebSocket and display real-time updates"""
    uri = "ws://localhost:8000/api/v1/monitoring/ws"

    print("=" * 70)
    print("  REAL-TIME MONITORING")
    print("=" * 70)
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected! Watching for events...\n")

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                timestamp = datetime.now().strftime("%H:%M:%S")

                if data['type'] == 'initial_state':
                    health = data['data']
                    print(f"[{timestamp}] Initial State:")
                    print(f"  Status: {health['status']}")
                    print(f"  Requests: {health['total_requests']}")
                    print(f"  Errors: {health['total_errors']}")
                    print(f"  Cost: ${health['daily_cost']:.4f}")
                    print()

                elif data['type'] == 'health_update':
                    health = data['data']
                    print(f"[{timestamp}] Health Update:")
                    print(f"  {health['total_requests']} requests | "
                          f"{health['total_errors']} errors | "
                          f"{health['avg_response_time']:.0f}ms avg | "
                          f"${health['daily_cost']:.4f}")

                elif data['type'] == 'api_call':
                    call = data['data']
                    status_icon = '✓' if call['status_code'] < 400 else '✗'
                    print(f"[{timestamp}] {status_icon} API Call: "
                          f"{call['method']} {call['endpoint']} - "
                          f"{call['status_code']} - {call['duration_ms']:.0f}ms")

                elif data['type'] == 'db_query':
                    query = data['data']
                    print(f"[{timestamp}] 🗄️  DB Query: "
                          f"{query['description'][:50]} - "
                          f"{query['execution_time_ms']:.0f}ms")

                elif data['type'] == 'error':
                    error = data['data']
                    print(f"\n{'='*70}")
                    print(f"[{timestamp}] ❌ ERROR DETECTED")
                    print(f"  Type: {error['error_type']}")
                    print(f"  Endpoint: {error['endpoint']}")
                    print(f"  Message: {error['message']}")
                    print(f"{'='*70}\n")

    except websockets.exceptions.ConnectionClosed:
        print("\n⚠️  Connection closed by server")
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(monitor())
