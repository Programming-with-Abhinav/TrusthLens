# TrustLens

TrustLens is a browser-based claim checker and URL safety scanner with a user-triggered long-page summarizer. See the [Product Requirements Document](docs/PRD.md) for product scope and summarizer requirements.

## Development status

Ready for local development and launch validation.

## Run the demo

The FastAPI app serves both the static website and API on port 5500:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 5500
```

Open `http://localhost:5500`. API documentation is available at `http://localhost:5500/docs`.

## Summarize a page

- Paste article text into **Summarize a page**, or use the extension popup's **Summarize page** button to extract selected text or visible article content.
- Paste a Wikipedia article URL in the page-text field to retrieve its plaintext through the MediaWiki API and receive section summaries.
- Choose a short or medium summary. Without `GEMINI_API_KEY`, the API selects key sentences directly from the supplied text; with a key it uses Gemini with source-only instructions and falls back to extraction if the request fails.
- Summarization is user-triggered. Inputs over 50,000 characters are truncated and the response identifies that; raw text is not persisted. Only the summary cache and generic activity entry are stored.

The endpoint is `POST /api/summarize` with `{ "text": "...", "url": "https://example.com/article", "length": "short" }` (`url` is optional and `length` may be `short` or `medium`).

Set `GEMINI_API_KEY` in the root `.env` to enable optional LLM mode. Extractive mode requires no external API key.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q test_main.py
```