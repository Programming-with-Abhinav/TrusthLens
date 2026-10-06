# TrustLens AI — Prototype

## Run
    pip install -r requirements.txt
    export GOOGLE_API_KEY=your_key      # Windows: set GOOGLE_API_KEY=your_key
    uvicorn main:app --reload --port 8000
Open http://localhost:8000

Enable **Fact Check Tools API** and **Web Risk API** in Google Cloud and use one API key.
Without a key the app runs in Demo mode (try "5G ..." / "vaccine ..." claims).

## Chrome extension
chrome://extensions → Developer mode → Load unpacked → select `extension/`.
Select any sentence on a page to see the Shadow-DOM verdict badge.

## Project structure
    main.py              FastAPI backend (Fact Check + Web Risk + cache/limiter/audit)
    static/              index.html, style.css, app.js  (web demo)
    extension/           manifest.json, content.js, popup.html/css/js  (Chrome MV3)
    Dockerfile, docker-compose.yml   one-command run:  docker compose up --build
    test_main.py         run:  pytest
    .env.example         copy to .env and add GOOGLE_API_KEY
