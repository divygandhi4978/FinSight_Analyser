# On Slash /api

### Login

| Endpoint               | Purpose                    |
| ---------------------- | -------------------------- |
| `POST /signup`         | Create user account        |
| `POST /login`          | Authenticate user          |
| `POST /logout`         | Invalidate session/token   |
| `POST /otp/send`       | Send OTP (login / reset)   |
| `POST /otp/verify`     | Verify OTP                 |
| `POST /password/reset` | Reset password             |
| `GET /me`              | Get logged-in user profile |

### 👤 2. User Profile & Preferences

| Endpoint                         | Purpose                     |
| -------------------------------- | --------------------------- |
| `GET /profile`                   | Fetch user profile          |
| `PUT /profile`                   | Update profile info         |
| `GET /subscription`              | Get current plan            |
| `GET /consumption`               | Get credits + report usage  |
| `GET /notifications/preferences` | Get alert/email preferences |
| `PUT /notifications/preferences` | Update preferences          |

### ⭐ 3. Watchlist

| Endpoint       | Purpose                       |
| -------------- | ----------------------------- |
| `GET /`        | Get user watchlist            |
| `POST /add`    | Add company to watchlist      |
| `POST /remove` | Remove company from watchlist |

### 🏢 4. Company Discovery

| Endpoint                | Purpose                           |
| ----------------------- | --------------------------------- |
| `GET /search`           | Search company by name / ticker   |
| `GET /:companyId/basic` | Minimal company identity (header) |

### 📊 5. Company Insight (CORE PRODUCT)

| Endpoint                     | Purpose                            |
| ---------------------------- | ---------------------------------- |
| `GET /:companyId`            | Fetch latest Company Insight page  |
| `POST /:companyId/generate`  | Generate insight (first time)      |
| `POST /:companyId/recompute` | Force recompute (consumes report)  |
| `GET /:companyId/status`     | Check if insight exists / is fresh |

### Notifier Client Side

| Endpoint        | Purpose                                |
| --------------- | -------------------------------------- |
| `GET /`         | List user notifications (latest first) |
| `GET /settings` | Get alert/email preferences            |
| `PUT /settings` | Update alert/email preferences         |

### Notifier admin side

| Endpoint                  | Purpose                     |
| ------------------------- | --------------------------- |
| `GET /filings/today`      | Get today’s filing updates  |
| `POST /filings/send`      | Trigger daily filing emails |
| `POST /filings/mark-sent` | Mark filings as emailed     |

### 💳 9. Credits & Usage (Read-Only for Client)

| Endpoint       | Purpose                |
| -------------- | ---------------------- |
| `GET /balance` | Current credit balance |
| `GET /usage`   | Report usage summary   |

### 🧠 10. AI Summary (Controlled Access)

| Endpoint                      | Purpose                |
| ----------------------------- | ---------------------- |
| `GET /summary/:companyId`     | Get AI analyst summary |
| `POST /regenerate/:companyId` | Regenerate AI summary  |

### Exports

| Endpoint                           | Purpose               |
| ---------------------------------- | --------------------- |
| `POST /company/:companyId/pdf`     | Export insight as PDF |
| `POST /company/:companyId/ic-memo` | Generate IC memo      |

### Admin

| Endpoint                      | Purpose         |
| ----------------------------- | --------------- |
| `POST /recompute/company/:id` | Force recompute |
| `GET /health`                 | System health   |
| `GET /stats`                  | Usage metrics   |