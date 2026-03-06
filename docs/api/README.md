# DebtSense API Documentation

DebtSense exposes a RESTful API under the `/api/v1` prefix. All endpoints return JSON and require `Content-Type: application/json` for request bodies. Authenticated endpoints expect a Bearer token in the `Authorization` header.

## Base URL

```
https://app.debtsense.io/api/v1
```

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require a valid JWT access token:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the authentication endpoints and expire after 30 minutes. Use the refresh token endpoint to obtain a new access token.

---

## Endpoint Groups

| Group | Base Path | Description |
|-------|-----------|-------------|
| **Auth** | `/api/v1/auth` | User registration, login, token refresh, password reset |
| **Users** | `/api/v1/users` | User profile management, account settings, preferences |
| **Debts** | `/api/v1/debts` | CRUD operations for user debts (credit cards, loans, mortgages) |
| **Income** | `/api/v1/income` | Income source management and tracking |
| **Expenses** | `/api/v1/expenses` | Expense tracking, categorization, and recurring expenses |
| **Financial Engine** | `/api/v1/financial-engine` | Debt payoff calculations (avalanche, snowball, custom strategies) |
| **Simulations** | `/api/v1/simulations` | What-if scenario modeling for debt repayment plans |
| **AI Advisor** | `/api/v1/ai-advisor` | AI-powered financial advice and personalized recommendations |
| **Analytics** | `/api/v1/analytics` | Financial dashboards, trends, and aggregated insights |
| **Notifications** | `/api/v1/notifications` | User notification preferences and notification history |

---

## Auth (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Create a new user account |
| `POST` | `/login` | Authenticate and receive JWT tokens |
| `POST` | `/refresh` | Refresh an expired access token |
| `POST` | `/logout` | Invalidate the current refresh token |
| `POST` | `/forgot-password` | Request a password reset email |
| `POST` | `/reset-password` | Reset password with a valid reset token |

## Users (`/api/v1/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/me` | Get current user profile |
| `PUT` | `/me` | Update current user profile |
| `DELETE` | `/me` | Delete current user account |
| `PUT` | `/me/password` | Change password |
| `GET` | `/me/preferences` | Get user preferences |
| `PUT` | `/me/preferences` | Update user preferences |

## Debts (`/api/v1/debts`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all debts for the current user |
| `POST` | `/` | Create a new debt entry |
| `GET` | `/{debt_id}` | Get a specific debt by ID |
| `PUT` | `/{debt_id}` | Update a debt entry |
| `DELETE` | `/{debt_id}` | Delete a debt entry |
| `GET` | `/summary` | Get aggregated debt summary |

## Income (`/api/v1/income`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all income sources |
| `POST` | `/` | Add a new income source |
| `GET` | `/{income_id}` | Get a specific income source |
| `PUT` | `/{income_id}` | Update an income source |
| `DELETE` | `/{income_id}` | Delete an income source |

## Expenses (`/api/v1/expenses`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all expenses (supports filtering and pagination) |
| `POST` | `/` | Record a new expense |
| `GET` | `/{expense_id}` | Get a specific expense |
| `PUT` | `/{expense_id}` | Update an expense |
| `DELETE` | `/{expense_id}` | Delete an expense |
| `GET` | `/categories` | List expense categories |
| `GET` | `/summary` | Get expense summary by category and period |

## Financial Engine (`/api/v1/financial-engine`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/calculate` | Calculate optimal debt payoff plan |
| `POST` | `/compare-strategies` | Compare avalanche vs. snowball vs. custom strategies |
| `GET` | `/strategies` | List available repayment strategies |

## Simulations (`/api/v1/simulations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List saved simulations |
| `POST` | `/` | Create a new what-if simulation |
| `GET` | `/{simulation_id}` | Get simulation results |
| `DELETE` | `/{simulation_id}` | Delete a simulation |
| `POST` | `/run` | Run a simulation without saving |

## AI Advisor (`/api/v1/ai-advisor`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/advice` | Get personalized financial advice |
| `POST` | `/chat` | Interactive chat with the AI advisor |
| `GET` | `/history` | Get advice history |

## Analytics (`/api/v1/analytics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Get dashboard data (debt overview, trends) |
| `GET` | `/debt-progress` | Get debt payoff progress over time |
| `GET` | `/spending-trends` | Get spending trend analysis |
| `GET` | `/projections` | Get financial projections |

## Notifications (`/api/v1/notifications`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all notifications |
| `PUT` | `/{notification_id}/read` | Mark a notification as read |
| `PUT` | `/read-all` | Mark all notifications as read |
| `GET` | `/preferences` | Get notification preferences |
| `PUT` | `/preferences` | Update notification preferences |

---

## System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Application health check (no auth required) |
| `GET` | `/api/docs` | Swagger UI (development only) |
| `GET` | `/api/redoc` | ReDoc documentation (development only) |
| `GET` | `/api/openapi.json` | OpenAPI schema (development only) |

---

## Common Response Formats

### Success Response

```json
{
  "data": { ... },
  "message": "Success"
}
```

### Error Response

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Paginated Response

```json
{
  "data": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

---

## Rate Limiting

- General API: 60 requests per minute per user
- Auth endpoints: 5 requests per minute per IP
- AI Advisor: 10 requests per minute per user

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1709856000
```
