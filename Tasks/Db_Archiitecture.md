## Customers

```
{
  "_id": ObjectId,
  "userId": "uuid-v4",

  /* -------------------------
     Profile
  ------------------------- */
  "profile": {
    "fullName": "Divy Gandhi",
    "email": "divy@email.com",
    "phone": "+91XXXXXXXXXX",
    "username": "divyg"
  },

  /* -------------------------
     Authentication
  ------------------------- */
  "auth": {
    "passwordHash": "bcrypt_hash",
    "provider": "local | google",
    "emailVerified": true,
    "phoneVerified": false,
    "lastLoginAt": ISODate,
  },

  /* -------------------------
     OTP (LATEST ONLY)
  ------------------------- */
  "otp": {
    "purpose": "login | signup | reset",
    "channel": "email | sms",
    "otpHash": "hashed",
    "sentAt": ISODate,
    "expiresAt": ISODate,
    "attempts": 0
  },

  /* -------------------------
     API / Product Keys
  ------------------------- */
  "keys": {
    "publicKey": "pk_live_xxx",
    "secretKeyHash": "hashed",
    "rotatedAt": ISODate
  },

  /* -------------------------
     Meta & Status
  ------------------------- */
  "status": "active | suspended | deleted",
  "createdAt": ISODate,
  "updatedAt": ISODate,
  "lastActiveAt": ISODate
}
```

## Subscriptions

```
{
  "_id": ObjectId,
  "userId": "uuid-v4",

  "plan": "free | premium ",
  "status": "active | expired | cancelled",

  "billing": {
    "provider": "razorpay",
    "subscriptionId": "sub_xxx",
    "lastPaymentId": "txn_xxx"
  },

  "startedAt": ISODate,
  "expiresAt": ISODate,

  "createdAt": ISODate,
  "updatedAt": ISODate
}
```

# Usage

```
{
  "_id": ObjectId,
  "userId": "uuid-v4",

  /* -------------------------
     Credit Wallet
  ------------------------- */
  "credits": {
    "totalAllocated": 1000,
    "used": 340,
    "remaining": 660
  },

  /* -------------------------
     Report-Based Limit
  ------------------------- */
  "reportLimit": {
    "limit": 50,
    "period": "monthly"
  },

  /* -------------------------
     Report Usage
  ------------------------- */
  "reportUsage": {
    "used": 12,
    "periodStart": ISODate,
    "periodEnd": ISODate
  },

  /* -------------------------
     Reset Rules
  ------------------------- */
  "resetRules": {
    "credits": "monthly | weekly | none",
    "reportUsage": "monthly"
  },

  "lastResetAt": ISODate,

  /* -------------------------
     Plan Context
  ------------------------- */
  "plan": "free | premium | pro",

  "createdAt": ISODate,
  "updatedAt": ISODate
}
```

## Notification History

```
{
  "_id": ObjectId,
  "userId": "uuid-v4",

  "type": "email | sms | in_app",
  "category": "alert | system | premium | marketing",
  "title": "Valuation Alert Triggered",
  "payload": {
    "companyId": ObjectId,
    "metric": "upside_percent",
    "value": 25
  },

  "status": "sent | failed | queued",
  "providerMessageId": "msg_xxx",

  "sentAt": ISODate
}

```

## Watchlist

```
{
  "_id": ObjectId,
  "userId": "uuid-v4",

  "companies": [
    {
      "companyId": ObjectId,
      "addedAt": ISODate
    }
  ],

  "createdAt": ISODate,
  "updatedAt": ISODate
}
```

## Event Change

```
{
  "_id": ObjectId,

  /* Company identity */
  "companyId": ObjectId,
  "ticker": "TCS",

  /* What kind of update */
  "type": "valuation | financials | risk | market | filing",

  /* What exactly changed */
  "field": "intrinsicValue | price | riskScore | earnings | annualReport | quarterlyResult",

  /* Optional delta */
  "oldValue": 4000,
  "newValue": 4200,

  /* Importance */
  "severity": "low | medium | high",

  /* Source */
  "source": "recompute | filing | price_move",

  /* Filing-specific control */
  "filing": {
    "filingType": "annual | quarterly | event",
    "period": "FY2024 | Q3FY25",
    "title": "Q3 FY25 Results"
  },

  /* Timing */
  "changedAt": ISODate,
  "expiresAt": ISODate,   // auto-delete after 3 days

  /* n8n state */
  "processed": false
}
```

## Pending to design the Company DB for all page insights
