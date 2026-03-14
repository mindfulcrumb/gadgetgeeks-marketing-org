# Department Context (Shared)

## Purpose
This file is loaded by every department agent. It contains the canonical facts about the business, brand, audience, and competitive landscape. If any department-specific prompt contradicts this file, this file wins.

---

## The Store

- **Name**: GadgetGeeks Pro
- **Domain**: gadgetgeekspro.myshopify.com
- **Live theme**: Refresh (#157805740283)
- **Shopify API version**: 2026-01 (GraphQL Admin only, never REST)
- **API helper**: Read Shopify data via `shopify_api.py` — never call the API directly from agent prompts

---

## Location & Market

- **Headquarters**: Tucson, Arizona, USA
- **Timezone**: America/Phoenix (MST, no daylight saving)
- **Primary Market**: Arizona — Tucson, Phoenix, Mesa, Scottsdale, Chandler, Gilbert, Tempe, Flagstaff
- **Secondary Market**: US Southwest (New Mexico, Nevada, Southern California, Utah, Colorado)
- **Tertiary Market**: National US (ships everywhere)
- **Local advantage**: We're a real Arizona business, not a faceless warehouse. Local trust matters for refurbished — people want to know someone nearby stands behind the product.
- **Local audience**: University of Arizona students, Tucson families, Phoenix metro commuters, ASU students, snowbirds (Oct-Apr), military families (Davis-Monthan AFB)

Every agent should consider the Arizona angle when creating content, copy, SEO, or social posts. "Refurbished phones Tucson" and "used iphone Arizona" are keywords we should own. Local content ranks faster and builds trust.

---

## Niche

Refurbished smartphones and accessories. We buy used phones, put them through a rigorous inspection and grading process, and resell them at a steep discount to retail. We also sell cases, chargers, screen protectors, and cables.

### Product Lines

| Category | Brands | Price Range |
|----------|--------|-------------|
| Phones | Apple iPhone (SE through 16 Pro Max), Samsung Galaxy (A-series, S-series, Z Flip/Fold), Google Pixel (7 through 9 Pro) | $149 - $899 |
| Accessories | Cases, screen protectors, chargers, cables, earbuds | $9.99 - $49.99 |

### Grading System
- **Excellent**: Looks new. No scratches, dents, or wear. Battery health 90%+.
- **Good**: Light scratches on screen or body. Not visible when screen is on. Battery health 85%+.
- **Fair**: Visible cosmetic wear. Fully functional. Battery health 80%+.

All grades include the same warranty and inspection.

---

## Value Propositions (Use These Everywhere)

1. **65-point inspection** — every phone tested across 65 checkpoints before it ships
2. **90-day warranty** — something breaks, we fix or replace it, no questions
3. **Free shipping** — on every order, no minimum
4. **30-day returns** — don't like it, send it back within 30 days for a full refund
5. **Eco-friendly** — buying refurbished keeps one more phone out of a landfill

These are the five pillars. Every product page, email, ad, and landing page should reference at least two of them.

---

## Brand Voice

### We sound like:
- A knowledgeable friend who happens to work in tech
- Trustworthy and straightforward — we say what we mean
- Slightly nerdy — we genuinely care about specs and phone minutiae
- Confident but not cocky — we know our stuff, we don't need to shout about it

### We never sound like:
- A used car salesman pushing a deal
- A corporate press release
- A breathless hype machine
- Condescending or elitist about tech knowledge

### Tone rules:
- Use contractions (we're, you'll, it's, don't)
- Short sentences are good. One-sentence paragraphs too.
- Specific numbers always ("saves you $347" not "saves you money")
- Talk about the customer's life, not our company
- Humor is fine, but never at the customer's expense
- Max 2 exclamation marks per piece of copy

---

## Target Audience

### Primary segments:

**1. Budget-Conscious Tech Buyers (40% of customers)**
- Age 25-45, income $40-80K
- Want a good phone without the $1,200 price tag
- Research-heavy — they compare specs, read reviews, check multiple sellers
- Key objection: "Is refurbished just a fancy word for broken?"
- Convince with: inspection process, warranty, specific condition details

**2. Eco-Conscious Consumers (25% of customers)**
- Age 22-38, skew female
- Already buy secondhand clothing, furniture, etc.
- Want to reduce e-waste but won't sacrifice quality
- Key objection: "Will it actually last as long as a new phone?"
- Convince with: battery health data, warranty, environmental impact stats

**3. Parents Buying Kids' First Phones (20% of customers)**
- Age 35-50, buying for kids aged 10-16
- Don't want to spend $1,000 on a phone that might get dropped in a toilet
- Care about durability and value more than bleeding-edge specs
- Key objection: "What if my kid breaks it in a week?"
- Convince with: 90-day warranty, case bundles, Fair grade as entry point

**4. Small Business / Side-Hustle Buyers (15% of customers)**
- Buying 2-5 phones at a time for employees or resale
- Price-sensitive, want volume discounts
- Key objection: "Can I trust consistent quality across multiple units?"
- Convince with: grading consistency, bulk order support, business accounts

---

## Competitors

| Competitor | Strength | Weakness | How We Win |
|------------|----------|----------|------------|
| Back Market | Brand recognition, huge selection | Marketplace model (inconsistent seller quality) | We inspect every phone ourselves — no third-party sellers |
| Swappa | Peer-to-peer trust, community | No warranty, buyer assumes risk | Our 90-day warranty removes all risk |
| Gazelle | Simple trade-in process | Limited selection, higher prices | Wider selection, better prices, same quality |
| Decluttr | Fast quotes, easy selling | Generic listings, slow shipping | Detailed condition photos, fast free shipping |
| Amazon Renewed | Prime shipping, Amazon trust | Inconsistent quality, generic listings | 65-point inspection, real condition grades, humans who answer the phone |

---

## Key Metrics (Targets)

| Metric | Target |
|--------|--------|
| Conversion rate | 3-5% (Shopify avg is 1.4%) |
| Cart abandonment | Under 65% |
| Average order value | $150+ |
| Return rate | Under 5% |
| Email open rate | 25%+ |
| Email click rate | 3.5%+ |
| LCP | Under 2.5s |
| CLS | Under 0.1 |
| Lighthouse score | 90+ |

---

## Customer Language

Use phrases real customers use. Pull from `intel/customer-language.json` for the latest, but these patterns are evergreen:

- "works like new" (not "premium refurbished experience")
- "no scratches I can see" (not "pristine cosmetic condition")
- "battery lasts all day" (not "optimal battery performance")
- "half the price of new" (not "significant cost savings")
- "looks brand new honestly" (not "exceeds cosmetic expectations")

If you catch yourself writing something a customer would never say out loud, rewrite it.

---

## File Conventions

- Queue items for human approval: ````json // QUEUE_ITEM``` format
- Update JSON state files: ````json // UPDATE: path/to/file.json``` format
- Draft copy files go in each department's `drafts/` directory
- All dates in ISO 8601 (YYYY-MM-DD)
- All prices in USD

---

## Incident Log — MANDATORY FOR ALL AGENTS

**File**: `state/incident-log.json`

Every agent MUST read this file before running. It contains documented mistakes, root causes, fixes, and preventive rules. If you ignore an incident's preventive rule and repeat the same mistake, that's a fireable offense.

### Before You Run:
1. Read `state/incident-log.json`
2. Filter for incidents where your agent name appears in `agents_involved`
3. Check the `preventive_rule` field — these are binding rules you must follow
4. If you hit a new problem, log it (see format below)

### When to Log an Incident:
- A blog ships with broken links, bad copy, or missing images
- An API call fails and causes data loss or silent degradation
- An agent produces output that contradicts its own rules
- A workflow step is skipped or silently fails
- The human has to manually fix something an agent should have caught

### Incident Format:
```json
{
  "id": "INC-[next number]",
  "date": "[YYYY-MM-DD]",
  "severity": "[critical|high|medium|low]",
  "department": "[department name]",
  "agents_involved": ["[agent names]"],
  "title": "[short description]",
  "what_happened": "[factual description of the failure]",
  "root_cause": "[why it happened]",
  "fix_applied": "[what was done to fix it]",
  "lesson": "[what we learned]",
  "preventive_rule": "[binding rule to prevent recurrence]",
  "status": "[resolved|open|monitoring]"
}
```

### Severity Levels:
- **critical**: Customer-facing damage — broken links on live site, wrong content published, data exposed
- **high**: Internal damage — credentials leaked, workflows broken, silent failures
- **medium**: Quality issue — copy violations, missed checks, process gaps
- **low**: Minor — cosmetic issues, non-blocking warnings

The GM reads the full log weekly and includes an incident summary in the weekly report. The boss delegates fixes based on this log.
