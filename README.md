# Product catalog with AI recommendations — Vercel deployment

This version is restructured so the **entire app** (React frontend + Flask backend)
deploys to Vercel as a single project — no separate hosting needed.

```
.
├── vercel.json          tells Vercel how to build the frontend and route /api/*
├── api/
│   ├── index.py          Flask app — Vercel runs this as a serverless function
│   └── requirements.txt  Python deps for the function
└── frontend/
    ├── src/               React source (App.jsx, api.js, main.jsx, index.css)
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## How the routing works

- Vercel builds `frontend/` with `npm run build` and serves the static output
  (`frontend/dist`) for every request.
- Any request to `/api/...` is instead routed to `api/index.py`, which Vercel
  runs as a Python serverless function. Flask's own routes (`/api/products`,
  `/api/recommend`, `/api/health`) handle it from there.
- This means the **same `/api` paths work in both local dev and production** —
  the frontend code never needs to know which environment it's in.

## Deploying

### 1. Push this structure to GitHub

Replace your repo's contents with this layout (delete the old `backend/` folder
if you had one structured differently — `api/` replaces it).

### 2. Import the repo in Vercel

- Go to vercel.com → **Add New** → **Project** → import your GitHub repo.
- Vercel will detect `vercel.json` automatically. You should **not** need to
  manually set Root Directory, Build Command, or Output Directory — they're
  all defined in `vercel.json`.

### 3. Add your OpenAI key as an environment variable (critical step)

There is no `.env` file in production — Vercel does not read it, and you
should never commit one. Instead:

1. In the Vercel dashboard, go to your project → **Settings** → **Environment Variables**
2. Add:
   - Key: `OPENAI_API_KEY`     Value: `sk-your-real-key`
   - Key: `OPENAI_MODEL`       Value: `gpt-4o-mini`
3. Apply to **Production** (and Preview/Development if you want those to work too)
4. Save

### 4. Redeploy

Environment variable changes only take effect on a **new** deployment.
Go to **Deployments** → click the **⋯** menu on the latest one → **Redeploy**.

### 5. Verify

Visit `https://your-project.vercel.app/api/health` — you should see:
```json
{"status": "ok", "openai_configured": true}
```
If `openai_configured` is `false`, the environment variable didn't save or
you haven't redeployed since adding it.

Then visit `https://your-project.vercel.app/` and try the search bar.

## Running locally (unchanged)

Local development still works the same two-terminal way:

**Terminal 1 — backend:**
```bash
cd api
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file in the `api/` folder for local use only (never commit it):
```
OPENAI_API_KEY=sk-your-real-key
OPENAI_MODEL=gpt-4o-mini
```
You'll also need `python-dotenv` locally since Vercel doesn't need it but your
own machine does:
```bash
pip install python-dotenv
```
Then add these two lines near the top of `api/index.py` (only matters locally —
harmless in production since Vercel just won't find a `.env` file there):
```python
from dotenv import load_dotenv
load_dotenv()
```
Run it:
```bash
python index.py
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

## Common pitfalls this structure avoids

- **Blank page on Vercel**: happens when Vercel serves the raw `index.html`
  without running `npm run build` first (the `.jsx` import then fails silently
  in the browser). Fixed here by `vercel.json`'s explicit `buildCommand` and
  `outputDirectory`.
- **404 on every `/api/...` call**: happens when there's no `api/` folder at
  the repo root, or `vercel.json` doesn't rewrite `/api/*` to it. Fixed here
  by the `rewrites` rule.
- **401 "Incorrect API key"**: almost always means the key wasn't actually
  saved as a Vercel environment variable, or a deployment ran before the
  variable was added. Always redeploy after adding/changing it.
