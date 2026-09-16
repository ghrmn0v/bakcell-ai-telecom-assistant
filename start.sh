#!/bin/bash
echo "=========================================="
echo "  AI Telecom Assistant - Starting Server"
echo "=========================================="
echo ""
echo "Customer Dashboard: http://localhost:8000"
echo "Staff Dashboard:    http://localhost:8000/staff"
echo ""
echo "Press Ctrl+C to stop."
echo ""
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
