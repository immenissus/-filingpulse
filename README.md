# RoofLead

Lead generation SaaS for roofing contractors. Users define territories, receive homeowner leads, and manage subscriptions.

---

## 1. Purpose

RoofLead is a high-performance lead-generation SaaS platform designed specifically for roofing contractors. It connects active service providers with high-intent homeowner leads inside strictly defined geographical territories.

* **Frontend:** Next.js (Vercel)
* **Backend:** Express.js (Railway)
* **Database:** PostgreSQL (Supabase)
* **Payments:** Stripe subscriptions with free trials
* **Maps:** Google Maps API

---

## 2. Architecture

```
Frontend (Next.js)
        |
        v
Backend API (Express.js) <---> Stripe Subscriptions & Webhooks
        |               <---> Google Maps API
        v
Supabase PostgreSQL
```

### Component Responsibilities

* **Frontend (UI Only):** Resolves routes, presents interactive UI/UX, gathers user drawing coordinates, and handles user-facing dashboard interactions. Contains zero database queries or core business logic.
* **Backend API:** Orchestrates authentication, processes Stripe checkout sessions and webhooks, executes territorial geo-matching algorithms, and guards access to data layers.
* **Supabase Database (PostgreSQL):** Stores relational models for users, geographical circular territories, high-intent leads, and matched tables. Acts as the system source of truth.
* **Stripe:** Manages subscription tiers, trials, recurring invoicing, and notifies the backend of state changes (e.g. renewals, cancellations) via webhooks.
* **Google Maps API:** Handles client-side territory drawing, address autocomplete, and reverse-geocodes addresses to resolve coordinate pairs.

---

## 3. Folder Structure

```
RoofLead/
├── app/                  # Next.js App Router (pages & layouts)
├── components/           # Reusable client-side UI components
├── lib/                  # Client-side API fetch client wrappers and general utilities
├── hooks/                # Custom React state hooks (auth, territory fetching)
├── pages/                # Legacy Next.js pages router views (if applicable)
├── backend/
│   ├── routes/           # REST endpoint route registrations
│   ├── controllers/      # Route controllers mapping HTTP requests to services
│   ├── services/         # Decoupled core business logic (Stripe, matching engine)
│   └── middleware/       # JWT auth verification, logging, and error handlers
└── database/
    └── sql/              # Versioned raw DDL and database initialization schemas
```

### Folder Explanations

* **`components/`**
  Reusable visual UI components (e.g., standard mapping dashboards, tables, inputs, alert alerts).
* **`lib/`**
  Handles generic API call functions and helper configurations (e.g. supabase client initialization).
* **`routes/`**
  Defines endpoints mapped to HTTP verbs, binding middleware and controllers together.
* **`services/`**
  Contains stateless core business logic (e.g. territory validation, stripe payment logic) away from the routing layers.

---

## 4. Database Schema

The database relies on a relational Postgres schema. Essential core models:

### `users`
* `id` (UUID, Primary Key)
* `email` (VARCHAR, Unique)
* `stripe_customer_id` (VARCHAR, Nullable, Index)
* `subscription_status` (VARCHAR, Default: 'inactive')
* `created_at` (TIMESTAMPTZ)

### `territories`
* `id` (BIGINT, Primary Key)
* `user_id` (UUID, ForeignKey -> users.id, Cascade)
* `latitude` (NUMERIC)
* `longitude` (NUMERIC)
* `radius_km` (NUMERIC, Default: 50)
* `created_at` (TIMESTAMPTZ)

### `leads`
* `id` (BIGINT, Primary Key)
* `address` (TEXT)
* `latitude` (NUMERIC)
* `longitude` (NUMERIC)
* `status` (VARCHAR, Default: 'new')
* `created_at` (TIMESTAMPTZ)

---

## 5. API Endpoints

### Auth Endpoints

#### `POST /auth/signup`
* **Purpose:** Registers a new user account inside Supabase Auth.
* **Input:** `{"email": "user@example.com", "password": "securepassword"}`
* **Output:** `{"user_id": "uuid", "email": "user@example.com", "token": "jwt-token"}`

#### `POST /auth/login`
* **Purpose:** Authenticates user credentials and returns a session JWT.
* **Input:** `{"email": "user@example.com", "password": "securepassword"}`
* **Output:** `{"user_id": "uuid", "token": "jwt-token"}`

### Stripe Billing Endpoints

#### `POST /checkout/create-session`
* **Purpose:** Creates a Stripe Checkout Session to initiate a subscription free-trial.
* **Input (Headers: Authorization Bearer):** `{"price_id": "price_12345"}`
* **Output:** `{"checkout_url": "https://checkout.stripe.com/..."}`

#### `POST /stripe/webhook`
* **Purpose:** Process Stripe webhook updates (e.g., cancellations, trial periods expiring).
* **Input:** Stripe Event raw binary payload (requires signature verification header).
* **Output:** `{"received": true}`

### Territories Endpoints

#### `GET /territories`
* **Purpose:** Returns a list of circular territories registered by the authenticated user.
* **Input:** JWT Token in headers.
* **Output:** `[{"id": 1, "latitude": 30.267, "longitude": -97.743, "radius_km": 50.0}]`

#### `POST /territories`
* **Purpose:** Registers a new circular territory for the contractor.
* **Input:** `{"latitude": 30.267, "longitude": -97.743, "radius_km": 50.0}`
* **Output:** `{"id": 1, "latitude": 30.267, "longitude": -97.743, "radius_km": 50.0, "status": "created"}`

### Leads Endpoints

#### `GET /leads`
* **Purpose:** Retrieves a collection of matched homeowner leads inside the contractor's territories.
* **Input:** JWT Token in headers.
* **Output:** `[{"id": 42, "address": "123 Main St, Austin, TX", "status": "new", "created_at": "..."}]`

---

## 6. Main User Flows

### Sign Up & Onboarding Flow
```
User registers
     ↓
Account created in Supabase Auth
     ↓
Redirected to Stripe Checkout (Free Trial setup)
     ↓
Webhook captures checkout.session.completed
     ↓
`subscription_status` set to 'active'
     ↓
Contractor defines territories (lat, lng, radius)
     ↓
System matches leads within bounds and pushes alerts
```

### Lead Matching Flow
```
New lead enters system
     ↓
Extract latitude & longitude coordinates
     ↓
Perform Great-Circle distance query on `territories`
     ↓
Locate active users with overlapping circular boundaries
     ↓
Insert lead matches & trigger immediate email/web push
```

---

## 7. Environment Variables

Configure these keys inside your root `.env` (or cloud service variable dashboard):

* **`SUPABASE_URL`**
  The endpoint URL for your hosted Supabase project. Required by both Vercel and Railway.
* **`SUPABASE_KEY`**
  The public/secret API key used to read/write columns inside PostgreSQL.
* **`STRIPE_SECRET_KEY`**
  The cryptographically secure server-side API token used to create Checkout Sessions. **Never expose this to the frontend.**
* **`STRIPE_WEBHOOK_SECRET`**
  The signing secret generated by Stripe CLI or Stripe Dashboard used to verify webhook payload integrity.
* **`GOOGLE_MAPS_API_KEY`**
  Client-side API key utilized by the Next.js frontend to render interactive Map dashboards and capture address selections.
* **`FRONTEND_URL`**
  Domain of the Next.js app (e.g., Vercel) used to handle OAuth redirects and Stripe success/cancel callbacks.
* **`BACKEND_URL`**
  Domain of the Express API running on Railway.

---

## 8. Business Rules

* **Single Territory Definition:** A single territory is defined by exactly one coordinate center (`latitude`, `longitude`) and a radial distance (`radius_km`).
* **Default Radial Reach:** If a contractor does not specify a boundary size, the system defaults the radial reach to **50 kilometers**.
* **Overlap Exclusivity:** To prevent saturated bidding, users **cannot create overlapping territories** that cross other territories they own.
* **Active Paywall Gate:** Subscription status is verified at every API boundary. Active territories require a subscription status of `active` or `trialing`.
* **Lead Target Locking:** Leads are exclusively dispatched to contractors with active subscription statuses. If a match occurs but a subscription is delinquent, the lead is held.

---

## 9. Current Tech Stack

* **Frontend:** Next.js (React), TypeScript, Tailwind CSS, Google Maps SDK.
* **Backend:** Express.js, Node.js.
* **Database:** Supabase PostgreSQL (utilizing standard geometric extensions).
* **Hosting:** Vercel (Frontend), Railway (Backend API).
* **Payments:** Stripe Subscriptions (Billing portal & automated subscription states).

---

## 10. Known Issues / TODO

* **Notifications Missing:** Immediate SMS/email notification dispatches are currently mock placeholders.
* **Overlap Verification Gap:** Territory overlap checks are currently enforced on client-side math but need rigid server-side execution.
* **Webhook Retry Logic:** Stripe webhook route lacks backoff handling for temporary database lockouts.

---

## 11. Development Principles

* **Backend Encapsulation:** Core business logic, Stripe pricing rules, and geofence computation belong strictly in backend services.
* **Client Isolation:** The frontend must never handle Stripe secret keys or directly read/write raw database lines.
* **Reusability:** Visual elements (drawers, maps, lists) should be isolated inside modular React components.
* **Serialization Integrity:** All backend API JSON responses must strictly serialize properties as `camelCase`.

---

## 12. Important Files

* **`backend/routes/stripe.ts`**
  Initializes checkout sessions, verifies Stripe signatures, and handles webhook callback updates.
* **`services/territoryService.ts`**
  Handles territory CRUD operations and executes matching algorithms using SQL great-circle distance formulas.
* **`lib/supabase.ts`**
  Initializes Supabase connection clients and coordinates backend authentications.

---

## AI Context

This is a lead-generation SaaS for roofing contractors.

* **Frontend contains no business logic.** The Next.js UI is entirely stateless; all calculations happen on the server.
* **Stripe secrets live only in the backend.** Client-side checkout relies solely on Redirect Session URLs returned from Express.
* **Territory radius is stored in kilometers.**
* **PostgreSQL is the source of truth.** No local cached or session records override database states.
* **Subscription status determines access.**
* **Never duplicate logic already in `services/`.** Always import and delegate routines to existing service modules.
* **Prefer modifying existing files over creating new ones.** Keep the directory footprint tight and leverage existing structures.
