"""
AI Telecom Assistant — Launcher
Run this script to start the server.
"""
import uvicorn
import os

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

print("=" * 50)
print("  AI Telecom Assistant")
print("=" * 50)
print()
print("  Customer Dashboard: http://localhost:3001")
print("  Staff Dashboard:    http://localhost:3001/staff")
print()
print("  Press Ctrl+C to stop.")
print()

uvicorn.run("main:app", host="0.0.0.0", port=3001, reload=False)
