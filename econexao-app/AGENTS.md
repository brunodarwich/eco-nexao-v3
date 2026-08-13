# ECOnexão Expo app

Read and follow the repository root `AGENTS.md` first.

This app currently uses Expo SDK 54 as declared in `package.json`. Use the exact SDK 54 documentation at https://docs.expo.dev/versions/v54.0.0/ for implementation work. Do not upgrade Expo as part of backend integration tasks; an upgrade requires a separate accepted ADR and regression task.

Keep server state out of `AppContext`. Supabase Auth/session access belongs in the dedicated auth/data layer, and domain data must be consumed through the FastAPI client unless an accepted ADR explicitly allows direct Supabase access.
