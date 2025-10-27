# Hawker Opportunity Score Platform

This project proposes a data-driven web application that identifies promising locations to open new hawker centres in Singapore. It computes a Hawker-Opportunity Score for each subzone based on population demand, existing hawker supply, and accessibility. Users (urban planners, entrepreneurs, policymakers) can interact with a map to explore opportunity scores, view detailed breakdowns, and compare subzones.

## Project Structure

```
hawker-opportunity-score/
├── backend/                 # Express.js backend with TypeScript
│   ├── src/
│   │   ├── main.ts         # Server entrypoint
│   │   ├── database/       # DB client and migrations
│   │   ├── models/         # Business objects/ORM models
│   │   ├── schemas/        # Request/response validation
│   │   ├── services/       # Business logic
│   │   ├── controllers/    # HTTP adapters
│   │   ├── routers/        # Route definitions
│   │   └── middlewares/    # AuthZ, error handling
│   └── .env               # Environment variables
├── frontend/              # React/Next.js frontend
│   ├── src/
│   │   ├── components/    # Reusable UI pieces
│   │   ├── contexts/      # React Context (auth, app state)
│   │   ├── data/          # Local fixtures/samples
│   │   ├── services/      # API client wrappers
│   │   ├── utils/         # Helpers, constants, hooks
│   │   └── screens/       # Main UI screens
│   │       ├── MainUI/    # End-user map & exploration
│   │       └── AdminUI/   # Admin console
│   └── public/            # Static assets
└── README.md
```

## Functional Requirements

### Display map
1.1 DisplaySubzones — Draw URA subzone polygons. Polygons are hoverable and clickable.
1.2 ChoroplethLayer — Shade subzones by Hawker-Opportunity Score with legend and normalized colour scale.
1.3 MapInteractionControls — Zoom, pan, and hover interactions on the subzone map.

### Display score and percentile
2.1 Hawker-OpportunityScore — Compute Dem, Sup, Acc, z-scale components, and produce Hᵢ with configurable weights and bandwidths.
2.2 ShowSubzoneRankPercentile — Show each selected subzone’s city-wide percentile for Hᵢ.

### Filtering and search
3.1 FilterByGeography — Filter visible subzones by region and optional subzone.
3.2 FilterByScoreQuantile — Filter by Top 10% / 25% / 50% or All; update legend accordingly.
3.3 SearchBySubzoneName — Autocomplete search; zoom and highlight on selection.

### Subzone details and comparison
4.1 ShowSubzoneDetails — For a selected subzone, display demographics, nearby hawker centres, nearby MRT/bus, Dem/Sup/Acc component values, final Hᵢ, and simple charts.
4.2 SubzoneComparison — Let users add up to two subzones to a tray and view side-by-side metrics with radar/table views. (a subpage in the main page map)

### Admin data operations and export
5.1 RefreshDatasets (Admin) — Reload official datasets and recompute scores; save a new snapshot.
5.2 ManageSnapshots (Admin) — List, view, and restore snapshots with version notes and timestamps.
5.3 ExportSubzoneDetails — Export the current subzone details view as PDF/PNG with metadata.

### Authentication and password flows
6.1 ClientRegistration — Register a client account.
6.2 UserLogin — Log in with email and password; idle session timeout enforced.
6.3 PasswordManagement — Change password while signed in; invalidate other sessions.
6.4 ResetForgottenPassword — “Forgot Password” email flow with one-time token and policy checks.

## Tech Stack

**Frontend:**

- React.js
- TypeScript
- Tailwind CSS

**Backend:**

- FastAPI
- Python
- MySQL

