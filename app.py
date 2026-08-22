"""
app.py — Deprecation Notice.
The production system has migrated from Streamlit to:
- FastAPI Backend (backend/main.py)
- React Frontend (frontend/src/App.jsx)
Streamlit is decommissioned in production.
"""

if __name__ == "__main__":
    print("=" * 70)
    print(" 🛡️  Visual Risk Intelligence Engine — Production Notice")
    print("=" * 70)
    print("Streamlit has been decommissioned from production in favor of:")
    print("  1. FastAPI Backend:  python backend/main.py")
    print("  2. React Frontend:   cd frontend && npm run dev")
    print("=" * 70)
