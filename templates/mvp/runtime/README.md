# MVP subscription runtime

`mvp_runtime.py` is copied unchanged into **every generated MVP** by the build pipeline. It holds the
security-critical parts of a subscription site so they are tested once here, not re-written by an LLM
per MVP. `site_main.py.tpl` is the fixed page template; the AI only supplies the site *content*
(validated by `services/mvp_site.py`).

## What every MVP gets

- Pages: landing (`/`), `/explore`, `/item/{id}`, `/pricing`, `/account`, checkout success/cancel.
- Free visitors see a preview; premium fields are removed **on the server** before a response is sent.
- Subscribers are proven by a signed cookie **and** an active Stripe subscription for this MVP.
- Price: 99p in the UK, scaled to local purchasing power and charged in the local currency
  (`COUNTRY_PRICES`). The browser only sends a country, never an amount.
- Placeholder content is labelled "Sample data" until real data is connected.

## Platform setup (Railway variables on the Causal Affect service)

| Variable | Purpose |
|---|---|
| `MVP_STRIPE_SECRET_KEY` | **Restricted** key (`rk_live_` / `rk_test_`) or `sk_test_`. A full `sk_live_` key is refused. |
| `MVP_STRIPE_PRODUCT_ID` | Optional `prod_...` so every checkout uses one product in your dashboard. |
| `MVP_STRIPE_PORTAL_LOGIN_URL` | Optional Stripe customer-portal login link (`https://billing.stripe.com/...`) for "Manage billing". |
| `MVP_STRIPE_AUTOMATIC_TAX` | Optional `true` to enable Stripe Tax (must be set up in Stripe first). |

Restricted key permissions: **Checkout Sessions: write**, **Subscriptions: read**, and
**Products: read** only if you set `MVP_STRIPE_PRODUCT_ID`. Grant nothing else.
Each MVP also receives a random `MVP_SESSION_SECRET` and its `MVP_PUBLIC_URL` automatically.
Without `MVP_STRIPE_SECRET_KEY` an MVP still runs; its pricing page shows "Subscriptions open soon".

Try it first with a `sk_test_` key and Stripe test cards.

## Maintaining the price table

Exchange rates drift. Review `COUNTRY_PRICES` periodically. `validate_price_table()` (run by the
tests) checks every entry against Stripe's minimum charge and a sensible GBP range. Settlement in
GBP means each price must stay above Stripe's 30p minimum after conversion. At these prices
Stripe's fixed fee takes a large share, especially in the cheapest countries.

Revenue from MVPs is recorded in GBP pence using `services/mvp_currency.py` (approximate rates,
original amount kept in `metadata_json`). A test keeps its rate table identical to the runtime's.

## Known limits

- Access is per device (cookie). Email login / magic links are a later step.
- A visitor can pick another country on the pricing page; a mismatch with the billing country is only logged.
- The Stripe key is shared by all MVPs. Stripe Connect or a platform-side billing service would isolate them.
- Rate limiting and the subscription cache are per process.
