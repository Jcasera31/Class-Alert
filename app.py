from app import create_app

# Vercel/WSGI entrypoint
app = create_app()

if __name__ == "__main__":
    # For local dev via `python app.py`
    app.run(host="0.0.0.0", port=5000, debug=True)
