# Frontend auth: manual verification checklist

Setup: `frontend/.env.local` has `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
Run the backend (`backend/`: `.\.venv\Scripts\python -m uvicorn app.main:app --port 8000`)
and the frontend (`frontend/`: `npm run dev`), then open http://localhost:5173.

## Secrets
- [ ] `git check-ignore frontend/.env.local` prints the path (ignored).
- [ ] `git ls-files frontend/.env.local` prints nothing (not tracked).
- [ ] The key in `.env.local` starts with `sb_publishable_` (or is the legacy anon key), never `sb_secret_` / service_role.
      The app throws on startup if a secret key is configured.
- [ ] After `npm run build`, `dist/assets/*.js` contains no `sb_secret_` value.

## Sign-up / sign-in / session / sign-out
- [ ] Sign up with a new email. With email confirmation on, the page says to check your email; the user appears in Supabase > Authentication > Users.
- [ ] Sign in with a confirmed user: "Signed in as <email>" appears.
- [ ] Wrong password shows an error message and stays signed out.
- [ ] Reload the page while signed in: still signed in (session restored).
- [ ] Sign out: back to the form; reload keeps you signed out.

## Bearer token to FastAPI
- [ ] Signed in, click "Load my profile (FastAPI)": the profile JSON shows your user id.
- [ ] DevTools > Network: the request to `/api/v1/profile/me` has `Authorization: Bearer <token>`.
- [ ] Signed out, calling the API returns `UNAUTHENTICATED` (401).
- [ ] No request goes from the browser to `<project>.supabase.co/rest/v1/...` (data goes through FastAPI only).

Known dependency: "Load my profile" needs the backend `.env` and database set up (Task 1 / db-role.sql).
