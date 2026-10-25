# Wind forecast evaluator (UK day-ahead)
AI tools (Claude) were used to help build this app.

## Files
- backend/main.py – FastAPI: pulls Elexon FUELHH (WIND) + WINDFOR, selects the forecast available at day-ahead cutoff, computes MAE/RMSE/bias/P95/MAPE. `/api/data`, `/api/latest`
- frontend/ – React (Vite, Recharts) dashboard
- Dockerfile – multi-stage build; FastAPI serves the built React app

## Run
docker build -t wind . && docker run -p 8000:8000 wind   # http://localhost:8000
Dev: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`; `cd frontend && npm i && npm run dev`

## Deploy
Vercel does not run Docker; use Heroku (`heroku stack:set container`, `heroku container:push web`) or Render/Fly.
Live app: <ADD LINK>

## Key assumption
Decision cutoff = 09:00 UTC on D-1 (configurable in UI; GB day-ahead gate closure ≈ 09:20 UK time). Forecast per target slot = latest publishTime ≤ cutoff.


  final link - https://kjhwr-ppzf.onrender.com/
