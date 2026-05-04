# Choose My Lawyer — MVP Requirements

**CHOOSE MY LAWYER PILOT**
**MVP Requirements Document**

19 April 2026

## Purpose

1. This document sets out the requirements for the development of the Choose My Lawyer (**CML**) MVP for the West Midlands pilot.

2. The objective of the MVP is not to build a fully featured product, but to:

  1. Validate that users will complete the journey;

  2. Validate that users will convert (*Proceed*/*Request a callback*);

  3. Generate real commercial and behavioural data; and

  4. Support a live PPC-driven pilot from 1 June 2026.

3. This is a commercial proof experiment and no more.

4. Success is defined as a functioning, measurable system that allows users to compare conveyancing providers and take action.

## Scope

### In Scope:

1. Practice area: **Residential conveyancing** only.

2. Geography: West Midlands Combined Authority (**WMCA**).

3. Go live date: **1 June 2026**.

4. User journey: As defined in the Figma prototype (latest version).

5. Core functionality:

  1. Landing page with clear access to query field;

  2. Conversational in take with structured questions;

  3. Results page (split between top five and all results);

  4. User actions:

    1. Proceed;

    2. Request callback;

  5. Auto-generated email referral;

  6. Subsequent auto-generated email notifications (see 5.6 below);

  7. Firm portal (pricing updates and review engagement); and

6. Data capture, analytics, and marketing tracking.

### Out of Scope

1. Expansion beyond conveyancing;

2. National rollout considerations;

3. Advanced UX/UI refinement;

4. Complex integrations (e.g. case management systems);

5. Automated onboarding flows for firms;

6. Payment handling; and

7. Any non-essential features not required for pilot validation.

## Key Principle

1. The MVP must prioritise speed, clarity and measurability over completeness.

2. Manual or simplified solutions are acceptable where they do not impact the core user journey or data capture.

## User Journey

### Source of Truth

1. The user journey is defined by the existing Figma prototype.

2. The MVP must replicate the Figma prototype journey and screens as closely as reasonably possible, including in design by using the existing corporate logos and colour palette:

**Teal**
- HEX: #0AE5F6
- RGB: 10, 229, 246
- CMYK: 58, 0, 0, 0
- Pantone: 2985 CP

**Navy**
- HEX: #080C64
- RGB: 8, 12, 100
- CMYK: 100, 86, 0, 35
- Pantone: 2748 CP

**Mint**
- HEX: #69E4B5
- RGB: 105, 228, 181
- CMYK: 41, 0, 31, 0
- Pantone: 3375 CP

**Purple**
- HEX: #9747FF
- RGB: 151, 71, 255
- CMYK: 54, 67, 0, 0
- Pantone: 265 CP

### High-Level Flow (consumer users)

1. User lands on site;

2. User starts intake;

3. User answers structured questions according to conveyancing question scheme (to be provided separately);

4. User is asked whether they want their search results ranked according to the default balanced scorecard or according to a prioritised scorecard (see section 5.3 below for scorecard details).

5. System processes inputs and generates results;

6. User views comparison of firms;

7. User selects:

  1. *Proceed*, or

  2. *Request a callback*;

8. Email referral to selected law firm with details of Callback request or Proceed (instruction);

9. User receives a copy of the email sent to their selected law firm(s) together with specific messaging relating to next steps;

10. User is contacted directly by their selected law firm if that firm’s conflict checks are clear;

11. If those conflict checks are not clear the firm is required to notify CML that they cannot act for the user. At which point the platform sends an email to the user, directing them back to their search results and asking them to select another firm;

12. If the conflict checks are clear but the user does not respond to the firm’s attempts to contact them, the firm is required to notify CML. At which point the platform sends an email to the user to chase up the requested action and to direct them back to their search results if they want to reconsider their choice of firm.

13. In the case of Callbacks where the firm has not notified CML of a failed call, an email is sent to the user at the end of the day the Callback took place, offering them the opportunity to instruct that firm by using the *Proceed* function;

14. In the case of instructions (*Proceed*) where the firm has not notified CML of failed engagement, after a set period of time the user will receive a follow-up email from the platform to check that the quoted price was honoured by the firm and to chase feedback on their experience by way of leaving a review of the firm on the CML platform.

### High-Level Flow (firms)

1. Firms that have signed up to the CML platform will have access to a portal that allows them to update their pricing, to check basic tracking data about Callbacks and instructions (Proceed) received and to engage with any reviews left about their firm.

## Functional Requirements

### Intake (Question Flow)

1. Structured question flow as per Figma prototype (question schema to be provided separately).

2. Forward and backward navigation (where appropriate).

3. The system must ensure all required fields are completed and inputs are in a valid format (e.g. numeric values, valid postcode structure) before allowing the user to proceed.

### Pricing Generation

1. Pricing will be generated using structured pricing data derived from firm transparency statements, interpreted using AI.

2. Prior to go-live, all firm pricing data must be normalised into a standardised database format, suitable for deterministic application (to be provided separately).

3. Not all transparency statements will fit the standardised format. Many won’t, either partly or in whole. Those cases must be manually normalised into the database structure so no system interpretation occurs post go live.

4. The system must:

  1. Apply pricing rules deterministically at runtime; and

  2. Produce consistent outputs for identical inputs.

5. The pricing model must be based on the standardised database, ensuring:

  1. Consistency across firms;

  2. Comparability of outputs; and

  3. Stability of system behaviour.

6. The pricing database must feed into the firm portal in order to support firm-side updates via a controlled input interface, ensuring:

  1. Ease of use for firms; and

  2. Prevention of invalid or system-breaking inputs.

7. No probabilistic or AI-generated pricing is permitted at runtime.

8. The system must handle incomplete or missing pricing data gracefully (e.g. excluding firms or flagging unavailable results)

### Ranking and display logic

1. The system must rank firms using a deterministic, rules-based approach that reflects multiple consumer choice factors, including both price and quality signals.

2. The system must not rely on subjective or dynamic judgment at runtime.

3. The ranking must consider the following factors:

  1. Reputation (review score, adjusted for volume);

  2. Price (as quoted);

  3. Complaints History (drawing data from decisions published by the Legal Ombudsman in relation to poor service);

  4. Regulatory History (drawing data from decisions published by the Solicitors Regulation Authority in relation to professional misconduct);

  5. Distance (proximity to user – if selected); and

  6. Number of offices (as an indicator of scale).

4. By default firms are ranked according to a **balanced scorecard** assessment of all choice factors. The scorecard score (out of 100) is displayed in the furthest right-hand column of the results grid. See Annex One for full detail on the balanced scorecard methodology.

5. Alternatively, the system permits the user to select a **prioritised scorecard** where the user can specify one choice factor as the most important instead of relying on the default balanced scorecard. Again, details on the methodology are set out in Annex One.

6. Either way, scores are calculated relative to other firms in the same results set rather than compared to any objective threshold. The results therefore compare the market rather than compare to any CML standard.

7. Results are displayed in two sections, as follows:

  1. First, a “top five” of firms the user can contact immediately. These are only firms that have signed up to CML and therefore have the *Request a callback* and *Proceed* functions.

***Note:*** To preserve ranking integrity and consumer trust, it is essential that the top five results are drawn from the full market ranking. In other words, all in-scope firms (whether signed up or not) are ranked according to the selected scorecard and then the top five of signed-up firms is extracted from that ranking.

      1. Second, below the top five results are the full set of all firms in scope of the particular enquiry. All firms in scope appear here, regardless of whether they are signed up to CML or not. Again, ranking is not influenced by whether they have joined the platform.

    1. The full set of results should be sortable, allowing the user to click at the top of any choice factor column and sort the results by that factor. Sort functionality is not required for the top five results.

### User Actions

1. **Proceed**

  1. User selects *Proceed* next to a firm;

  2. Confirmatory form pops up with next step details including asking user for their name and email address and asking user to confirm they want to share their matter details with the selected firm;

  3. User enters name and email address and confirms they want to proceed;

  4. Email autogenerated to provide matter details to firm. **Email to firm must be in the name of the user and not in the name of CML.** Email is sent to address registered in the CML database for the selected firm and a copy sent to the user;

  5. Lead generated, timestamped and recorded.

2. **Request Callback**

  1. User selects *Request a callback* next to a firm or firms;

  2. User can request contact from up to five firms;

  3. Confirmatory form pops up with next step details including asking user for their name, email address and telephone number as well as availability to receive a call over the next two working days. User is also asked to confirm they want to share their matter details with the selected firm(s);

  4. User enters name, email address, telephone number, availability and confirms they want to proceed;

  5. Email autogenerated to provide matter details to firm. **Email must be in the name of the user, not CML.** Email is sent to address registered in the CML database for the selected firm and a copy sent to the user;

  6. Lead generated, timestamped and recorded.

### Data Capture (Leads)

1. For each action, capture:

  1. Relevant user inputs, including contact details;

  2. Selected firm(s);

  3. Action type (Proceed / Callback);

  4. Timestamp,

2. Store in structured, accessible format.

### Email notifications (MVP Level)

1. Notify firm on lead generation;

2. Copy notification to user;

3. On a *Request a callback* action:

  1. the system must send a follow-up email to the user at the end of the same working day as the scheduled callback; and

  2. this notification must prompt the user to confirm whether or not contact was made by the firm (binary option) and to direct the user back to their search results if no contact occurred.

4. On a *Proceed* action:

  1. the system must send a follow-up email to the user after five working days post-action; and

  2. this notification must prompt the user to confirm whether or not contact was made by the firm (binary option), to direct the user back to their search results if no contact occurred or, if onboarding is underway, to remind the user about looking out for price drift and to prepare the user for a later feedback request from CML.

5. After a *Proceed* action the selected firm will carry out conflict checks to see if it can act for the user. If those conflict checks are not clear the firm must notify CML. On receipt of that notification the system must notify the user immediately and provide a direct link back to their original search results to enable further selection.

6. After successful onboarding, user feedback should be sought to enrich the data environment being built by CML. The system must send a follow-up email to the user two months after the *Proceed* action to request structured feedback on the user’s experience of that firm.

## Data Requirements

1. System must support:

  1. Firm dataset (name, pricing, coverage, attributes);

  2. User inputs; and

  3. Generated outputs (quotes, firm lists).

## Analytics and Monitoring Requirements

1. System must enable real-time or near real-time monitoring of user behaviour and pilot performance.

2. The founder must be able to monitor performance and answer key commercial and behavioural questions without engineering support.

**Key Questions the System Must Answer**

### Traffic and Engagement:

1. Number of users;

2. Time on site;

3. Preference for scorecards;

4. Responsiveness to email notifications.

### Funnel Performance

1. % starting intake;

2. % completing intake;

3. % reaching results;

4. % converting to *Proceed*; and

5. % converting to *Request a callback*.

### Drop-off Analysis

1. Where users exit; and

2. Which steps drive drop-off.

### Commercial Performance

1. Number of *Proceed* actions;

2. Number of *Request a callback* actions; and

3. Average *Request a callback* actions per user.

### Search Behaviour

1. Types of searches;
2. Price ranges generated; and

3. Firms returned per search.

### Functional Analytics Requirements

1. Track user interactions as discrete events;

2. Each event must include:

  1. Timestamp;

  2. Session ID; and

  3. Relevant inputs (where applicable),

3. Support:

  1. Funnel analysis;

  2. Conversion tracking; and

  3. Drop-off identification.

### Marketing and Conversion Tracking (Critical)

1. The system must support paid acquisition tracking and retargeting (where a user has clicked off the CML site and been retargeted through meta ads).

2. Specifically:

  1. Implement Meta Pixel across all pages;

  2. Pixel must fire on:

    1. Page views;

    2. Search completion;

    3. Results page view;

    4. Proceed action; and

    5. Callback request,

  3. Events must be structured to enable:

    1. Conversion tracking;

    2. Retargeting audiences; and

    3. Campaign optimisation.

### Monitoring Interface

1. Monitoring interface required (via third-party tools or equivalent).

2. Must provide:

  1. Near real-time visibility;

  2. Daily performance tracking; and

  3. No-code access.

3. No custom dashboard required for MVP

### Data Access

1. Data exportable (e.g. CSV).

2. Founder must be able to analyse independently.

## Non-Functional Requirements (MVP Level)

1. Results returned within a few seconds.

2. Stable for live pilot use.

3. Basic data protection compliance.

## Assumptions and Constraints

1. Speed prioritised over completeness.

2. Limited firm dataset.

3. Manual processes acceptable.

4. PPC-driven traffic.

5. ~90 day pilot.

## Billing and invoicing (pilot)

1. For the pilot phase, billing will be managed manually. Chargeable events (*Proceed* and *Request a callback* actions) will be recorded within the system and exported for invoicing on a periodic basis.

2. Invoices will be issued by CML to participating firms after a defined delay period following the trigger event, allowing firms sufficient time to make contact with the user and commence onboarding.

3. This approach is appropriate to the expected low transaction volumes during the pilot and ensures accuracy, control, and flexibility while the commercial model is validated.

4. For full platform launch, billing will be automated through integration with a payment service provider, enabling real-time tracking of chargeable events, automated invoicing, and streamlined payment collection.

## Success Criteria

1. End-to-end journey works without failure.

2. Results generate accurately.

3. Users can take action.

4. Leads successfully captured and delivered.

5. Analytics data available and usable.

6. Marketing tracking (including Meta Pixel) functioning correctly.

7. Pilot generates measurable conversion data.

**John Quentin**
Founder & CEO

**ANNEX ONE**
**CML Ranking Logic and Scorecard Methodology**

## Purpose

1. This Annex sets out the ranking methodology for Choose My Lawyer for the pilot MVP with regards to both the balanced scorecard and the prioritised scorecards.

2. It is intended to ensure that ranking is:

  1. deterministic;
  2. rules based;
  3. transparent at system level;
  4. consistent across identical searches; and
  5. aligned with the CML thesis of quality weighted consumer choice rather than lowest price alone.

3. This Annex should be read together with section 5.3 of the main Requirements Document.

## Core ranking principle

1. All in scope firms must first be ranked across the full market results set using the same balanced scorecard methodology or, if the user prefers, the prioritised scorecard. This principle is fundamental to ensuring consumers trust in the CML ranking logic as neutral, rules based and deterministic. **This one design concept underpins the long-term success of CML more than any other.**

2. The system must not apply any subjective judgment or discretionary override at runtime.

3. Identical inputs and identical underlying data must always produce identical ranking outputs.

4. The ranking model combines both relative and absolute factor scores. Where appropriate, factors are normalised within the results set; where factors represent independent risk or structural attributes, absolute scoring is applied. The overall ranking is therefore derived from a consistent combination of both approaches.

## Ranking factors and weights

1. Each firm receives a total ranking score out of 100.

2. For the default balanced scorecard, that score is made up of the following six factors:

  1. Reputation – 25%
  2. Price – 25%
  3. Complaints history– 15%
  4. Regulatory history – 15%
  5. Distance– 10%
  6. Number of offices – 10%

3. The prioritised scorecard approach is described in **section 16** below.

4. Weightings will be tested with consumers during May. For completeness, the rationale for selecting the above weightings for the default balanced scorecard is as follows:
**Reputation (25%)**Reputation is given a high weighting as it reflects aggregated consumer feedback and provides an accessible indicator of perceived service quality based on prior client experience.

**Price (25%)**Price is heavily weighted to ensure strong price competition within the results set, while not allowing the lowest-priced option to automatically outrank firms demonstrating stronger performance across other factors.

**Complaints History (15%)**Complaints History is included as a distinct measure of adjudicated service outcomes, reflecting findings of poor service by the Legal Ombudsman. It provides a structured and objective complement to reputation by capturing where service delivery has been formally assessed as falling below required standards.

**Regulatory History (15%)**Regulatory History is incorporated as a core professional conduct signal, ensuring that published findings of regulatory action are reflected within the ranking in a consistent and transparent manner.

**Distance (10%)**Distance is included as a meaningful factor because many consumers value proximity to their lawyer for accessibility and reassurance. This is the only factor that a user may elect to exclude from the ranking logic.

**Number of Offices (10%)**Number of offices is included as a light indicator of scale and geographic coverage, without allowing firm size to exert a disproportionate influence on the ranking.

## General scoring approach

1. This applies to both the balanced scorecard and the prioritised scorecard approach.

2. For each search:

  1. Identify all firms in scope.
  2. Collect the raw value for each factor for each firm.
  3. Convert each raw value into a normalised factor score on a 0 to 100 scale.
  4. Apply the fixed weight for each factor in the appropriate order, according to the selected scorecard.
  5. Sum the weighted factor scores to produce the final ranking score out of 100.
  6. Rank firms from highest total score to lowest total score, displaying that integer score on the furthest right-hand column on the search results grid.

3. This ranking produces the full market order.

4. The *“top five firms you can contact immediately”* are then extracted from that full ranking by applying the contactability filter only after the full market ranking has been completed. This is a critical sequence to avoid inadvertently undermining the “whole of market” and “fully independent” claim that underpin consumer trust in CML.

## Factor 1: Reputation

1. This factor is intended to reflect the consumer importance of reputation while avoiding distortion caused by very low review volumes.

2. For each firm, the system must capture:

  1. average review rating; and
  2. total number of reviews.

3. The source or sources of review data should be standardised across firms where possible.

4. Review count is adjusted using a scaling function (logarithm) so that additional reviews increase confidence but with diminishing impact.

5. This is achieved by starting with the review rating, then increasing it by a confidence-based uplift derived from review volume using a dampened log model to avoid volume dominating quality. This produces an **adjusted reputation value**.

6. The proposed MVP calculation is therefore:

**Adjusted Reputation Value = Rating × (1 +** ***k*** **× log(Review Count + 1))**

  1. The formula works as follows, using an example of firm with a review rating of 4.6 based on 200 reviews:

**Step 1 — Take the average rating**
- This is the firm’s review score averaged across all reviews left.
- This is the core measure of quality and forms the baseline of the score.
- Worked example: average review rating = 4.6.

**Step 2 — Add 1 to the review count**
- This ensures the calculation works correctly when a firm has very few or zero reviews (it avoids mathematical issues with log(0)).
- Worked example: adjusted review count = 201.

**Step 3 — Take the logarithm of that number to dampen volume**
- Apply the natural logarithm (**ln**) to the adjusted review count.
- Ln is used because it provides the smoothest diminishing returns curve.
- This dampens the impact of review volume, so that large firms do not dominate purely due to scale.
- Worked example: ln(201) = 5.3033 (rounded to 4 decimal places).
- *In implementation, calculations should be performed using full numerical precision, with no rounding applied.*

**Step 4 — Multiply by the confidence weighting factor (*****k*****)**
- This controls how much influence the dampened review volume has on the overall score. A smaller *k* reduces the impact of volume; a larger *k* increases it.
- For the purposes of the pilot and for reasons described below, a confidence weighting factor of 0.025 is applied.
- Worked example: 5.30330491 x 0.025 = 0.1326 (rounded).
- *As above, implementation requires full numerical precision.*

**Step 5 — Add 1 to the result**
- This produces a multiplier: 1 + (*k* × log(Review Count + 1)).
- This ensures the rating remains the baseline score, with review volume acting as a modifier (uplift) rather than replacing the rating.
- Worked example: 0.1326 + 1 = 1.1326 (rounded).

**Step 6 — Multiply the rating by this multiplier**
- This produces a single score that combines quality (rating) and confidence (review volume) in a controlled and balanced way that dampens the effect of volume to ensure comparison remains meaningful even at the upper end of review volumes.
- Worked example: 4.6 x 1.1326 = 5.21 (rounded for this Annex).
- *Note again, implementation requires full numerical precision and not rounding.*

  1. This produces an adjusted reputation value for each firm in the results set. In the worked example above, the adjusted reputation value of 5.21 (rounded) reflects a modest uplift from the base rating of 4.6, driven by the relatively high number of reviews for this particular firm.

  2. That adjusted reputation value (**ARV**) is then normalised across the results set to produce a score out of 100, as follows:

| Normalised Reputation Score | = | (Firm ARV – Lowest ARV in results set) | x100 |
| --- | --- | --- | --- |
|  |  | (Highest ARV in results set – Lowest ARV in results set) |  |

  3. That normalised reputation score out of 100 then feeds into the scorecard according to the appropriate weighting assigned to the choice factor of reputation. The weighting is determined by the user’s choice of adopting the default balanced scorecard (25% weighting) or a prioritised scorecard (the precise weighting being determined in that scenario by which particular choice factor is prioritised).

  4. Normalised factor scores should be calculated and stored with full numerical precision and should not be rounded to integers for internal ranking purposes. It is essential for calculating overall scorecard scores that the individual factor scores retain full precision.

  5. **Tie breaker logic –** not required at factor level. Two firms can carry through exactly the same normalised reputation scores to their overall scorecard scores. Tie breaker logic is applied at that top level.

  6. **Edge case scenario** **–** Although extremely unlikely to ever arise in the real-world scenario, if the highest and lowest adjusted reputation values in a results set are the same each firm is assigned a neutral normalised score of 50 for this factor.

  7. **Note on the calibration of the confidence weighting factor (*****k*****)** –

    1. When calculating the adjusted reputation value, the constant *k* is used to control the influence of review volume on the adjusted reputation score. For the MVP, *k* is fixed at 0.025.

    2. This specific calibration reflects a deliberate choice to ensure that review volume strengthens confidence in a firm’s rating without allowing scale to dominate quality. In setting this value, the objective is to preserve a quality-first ranking, while recognising that a rating supported by a larger number of reviews is generally more reliable than one based on limited feedback.

    3. The particular value was selected following calibration against representative scenarios, including a comparison between Firm A with a 5.0 rating based on 10 reviews Firm B with a 4.6 rating based on 200 reviews.

    4. At *k* = 0.02, the resulting scores were approximately Firm A = 5.24 and Firm B = 5.09. On this basis review volume was felt to have insufficient influence, with the higher-rated firm (Firm A) clearly dominating despite the significantly lower number of reviews.

    5. At *k* = 0.03, the resulting scores were approximately Firm A = 5.36 and Firm B = 5.33. At this level review volume was felt to exert too strong an influence, with the two firms producing near-equivalent scores despite Firm B’s lower rating.

    6. The selected value of *k* = 0.025 produces scores of approximately Firm A = 5.30 and Firm B = 5.21, providing a balanced outcome between these positions and ensuring that review volume strengthens confidence in a rating without allowing scale to come close to overriding quality.

    7. The selected value therefore provides a measured and proportionate influence for review volume, consistent with the platform’s principles of transparency, fairness, and balanced assessment.

## Factor 2: Price

1. This factor reflects the total expected price for the defined legal service.

2. Note in the prototype this choice factor is labelled “cost”. More accurately, it should be labelled “price”.

3. Price data is drawn from two sources and the ranking logic must accommodate both:

  1. System-estimated prices, derived from interpreting publicly available Transparency Statements scraped from firm websites (**Estimated Price**); and

  2. Firm-provided quoted prices (**Quoted Price**).

4. By comparing both, the platform is able to surface firms that offer the best price, adjusted for confidence in the reliability of that price.

5. This approach also incentivises firms to provide precise price data, increasing confidence in their pricing and therefore improving their price score, which feeds into their overall scorecard score and ranking.

6. For each firm, the system must calculate **Total Effective** **Price** as the total expected cost to the consumer for the defined legal service. That total price must be calculated as:

  1. **Legal fees** (as charged by the firm for its work);

  2. Plus **included disbursements**;

  3. Plus **applicable VAT**.

**Legal fees**

  1. Legal fees are determined according to price type, whether Estimated Price or Quoted Price.

  2. By applying a confidence adjustment factor to account for the greater price uncertainty of an Estimated Price, the system then calculates an **Effective Legal Fee** as follows:

    1. For Estimated Prices: ***P*****legal,effective =** ***P*****estimated x (1 +** ***c*****)**

    2. For Quoted Prices: ***P*****legal,effective =** ***P*****quoted**

Where *c* is the confidence adjustment factor applied to reflect lower certainty in estimated pricing.

  1. For the purposes of the pilot, the value of *c* is set at 0.075, reflecting that Quoted Prices carry higher reliability and user confidence than Estimated Prices. This represents a calibrated uncertainty premium applied to system-estimated prices, reflecting the expected variability between estimated and realised pricing outcomes. The value has been selected to ensure that:

    1. firm-provided quoted prices are meaningfully favoured;
    2. estimated prices remain competitive within the results set; and
    3. the adjustment does not distort underlying price competition.

**Disbursements**

  1. Disbursements are third-party costs incurred by the firm on the client’s behalf as part of delivering the legal service, excluding the firm’s own fees.

  2. All disbursements must be classified by the CML system as either Included or Excluded.

  3. **Included Disbursements**:

    1. Those which are ordinarily required to complete the defined legal service and capable of being determined at the point of user intake.

    2. They must be stored in the CML database as single values exclusive of VAT. They should not be stored as ranges or conditional estimates.

    3. Where disbursement data is incomplete or absent, the system must populate Included Disbursements using reasonable estimates derived from available information.

    4. Any such estimated disbursement values must be treated as subject to uncertainty and must be adjusted accordingly within the pricing model.

    5. In such cases, a confidence adjustment factor, *d*, must be applied to reflect the lower reliability of Estimated Disbursement values relative to firm-provided disbursement values. This adjustment must be applied to the aggregate value of Included Disbursements where such values are estimated or system-derived.

    6. For the purposes of the pilot, *d* is set at 0.02.

    7. The application of this adjustment must ensure that:

      1. firms providing complete and precise disbursement data are systematically favoured;

      2. incomplete or estimated disbursement data does not artificially reduce the Total Effective Price used for ranking; and

      3. comparability across firms is preserved.

    8. Some disbursements attract VAT and others do not. The VAT treatment for each item should be recorded when normalised into the database.

    9. Included Disbursements form part of the Total Effective Price used in ranking logic.

    10. They should be itemised in the price breakdown shown in the results field.

  4. **Excluded Disbursements**:

    1. Those which are conditional and cannot be reliably determined at the point of user intake.

    2. They must not be included in the ranking price calculation.

    3. The potential for any Excluded Disbursements must be clearly flagged to users in the price breakdown field with a link to a separate page on the platform that explains the CML classification rules regarding included and excluded items. The user should be reminded of this in the confirmatory form that pops up when they select *Proceed* or *Request a callback*, to remind users of what is and is not included in the price and to direct them to the article on the CML platform that generically explains in more detail.

**Total Effective Price construction**

  1. The Total Effective Price used for ranking must be calculated as follows:

***P*****effective =** ***P*****legal,effective + (*****P*****legal,effective x VAT) +** ***P*****included disbursements**

  1. As described above, VAT treatment of disbursements is varied but is specified in the back-end database. The function ***P*****included disbursements** represents the aggregate figure for all applicable disbursements derived from the database with VAT already applied as appropriate.

**Normalised Price Score**

  1. Once the Total Effective Price is derived, the price score is then calculated by relative comparison within the same results set to produce a score between 0 and 100:

| Normalised Price Score | = | (Pmax – Peffective) | x 100 |
| --- | --- | --- | --- |
|  |  | (Pmax – Pmin) |  |

Where:
***P*****max** = Highest Total Effective Price in the results set
***P*****min** = Lowest Total Effective Price in the results set
***P*****effective** = The Total Effective Price for this firm.

  1. Lower effective prices must result in higher normalised price scores.

  2. The normalised price score is then factored into the scorecard score with full numerical precision, according to the applicable weighting as selected by the user.

  3. As per the logic treatment of all other choice factors:

    1. Tie breakers are not required at choice factor level; and

    2. In the extremely unlikely event of all firms in the results set having the same Total Effective Price then all firms receive a normalised price score of 50 for that factor.

  4. This approach ensures that:

    1. firms with precise, user-specific pricing are systematically favoured;

    2. estimated pricing remains included to preserve market coverage;

    3. differences in price certainty are reflected transparently within the scoring model;

    4. the system incentivises adoption of structured pricing without requiring exclusion rules.

  5. The model aligns with the platform’s principles of:

    1. transparency;

    2. predictability; and

    3. rules-based outcomes.

## Factor 3: Complaints History

**LeO decisions**

  1. Decisions of the Legal Ombudsman (**LeO**) are a measure of the quality of service, with penalties given for service determined to be inadequate.

  2. Decisions are published on its website and a CSV download is publicly available. That provides structured data fields including the firm identifier, decision date, outcome (including whether poor service was found), and remedy details (including remedy type and remedy amount).
  3. For example:

  4. The treatment of complaints data within the system must adhere to the following principles:

    1. **Firm-level assessment** - Complaints History must be assessed at firm level only, with all relevant decisions aggregated to the firm entity.

    2. **Source-based inclusion** - Only decisions that are actively published by LeO may be included in the system. Where a decision is no longer published, it must be excluded and must not influence ranking outcomes.

    3. **Scope limitation (firm type)** – LeO adjudicates service complaints for a variety of legal professionals, some of whom are out of scope for CML. For example, barristers. Complaints History must be limited to LeO decisions relating to SRA-regulated firms only. The system must include only decisions where the service provider is classified as “**Firm SRA**” or “**ABS Firm SRA**” within the published dataset. All other provider types, including decisions relating to individual practitioners, must be excluded from the model and must not influence the Complaints History score.

    4. **Inclusion threshold (poor service)** - Only decisions in which poor service is found may contribute to the Complaints History score. Decisions in which poor service is not found must be excluded. This is a binary data input from the LeO dataset.

    5. **No editorial judgment** - The system may classify and structure complaints data using predefined, rules-based categories, but must not apply subjective or qualitative judgment. It must only reflect observable outcomes as published by LeO.

    6. **No inferred or constructed data** - The system must not infer complaint rates, success rates, or any proportional metrics (including complaints as a proportion of total matters handled). Only published decisions may be used.

    7. **Downside-only signal** - Complaints History must operate as a negative factor within the ranking model. Adverse outcomes reduce the score from a base of 100, but the absence of such outcomes does not result in any additional uplift beyond that baseline.

    8. **Structured aggregation** - Where multiple decisions about one firm are published, they must be aggregated using a simple additive model, with each decision contributing a predefined deduction to the overall score. No adjustment must be made for repetition, linkage or contextual relationship between decisions.

    9. **Transparency and traceability** - All complaints signals presented within the system must be traceable to their original source. Users must be provided with direct access to the relevant published decisions via a link to the LeO webpage.

    10. **Publication-based recency** - The inclusion of Complaints History is determined by its current publication status. No additional time-based weighting is applied beyond LeO’s publication policies.

  5. Published LeO decisions record the outcome of service complaints against firms and can include any of the following remedies:

    1. financial compensation, whether to compensate for financial loss or emotional distress;

    2. fee remedies (a specified reduction of fees);

    3. non-financial remedies (such as an apology, explanation or corrective action); and

    4. a finding as to whether the firm handled the original complaint reasonably (this is the consumers initial complaint to the firm).

  6. For the purposes of the model, qualifying LeO decisions are categorised in three stages:

    1. First, by Remedy Type. They are grouped into three severity bands (**non-financial remedy**, **fee remedy**, and **financial compensation**) to derive a score for Remedy Type. These severity bands reflect increasing seriousness from service failure without direct financial redress, to service failure requiring fee adjustment, to service failure requiring compensatory payment. Their assigned scores are set out below.

    2. Second, by Remedy Amount. This is simply stated as a numerical value band (e.g. £300-£749) or occasionally £0. Again, these bands will be assigned scores so that Remedy Amount also generates a score.

    3. Third, a finding that the firm did or did not handle the original complaint reasonably. This must be treated as an aggravating feature and applied as an additional fixed deduction to the after the Remedy Type and the Remedy Amount have already contributed.

  7. First step is assessing **Remedy Type**. In the LeO dataset, the various Remedy Types are stated in a single field with comma separators. The phrases are structured and consistent, so can therefore be mapped onto the three severity bands (with one exception) using a decoder table as follows:

| Remedy phrase | Severity band |
| --- | --- |
| No Remedy | (Special category) |
| Other | Non-pecuniary |
| To Apologise | Non-pecuniary |
| To complete work for the complainant | Non-pecuniary |
| To return papers | Non-pecuniary |
| To refund fees already paid | Fee remedy |
| To waive unpaid fees | Fee remedy |
| To limit fees to a specified amount | Fee remedy |
| To pay compensation for emotional impact and/or disruption caused | Financial compensation |
| To pay compensation of a specified amount for loss suffered | Financial compensation |
| To pay a specified amount for expenses the complainant incurred in pursuing the complaint | Financial compensation |
| To pay for someone else to complete the work | Financial compensation |
| To take (and pay for) any specified action in the interests of the complainant | Financial compensation |
| To pay interest on compensation | Financial compensation |
| To pay interest on monies held | Financial compensation |

  8. The exception item is No Remedy, which is assigned to special category. This is because although LeO decided no remedy was required it still found that poor service had occurred. This needs to be reflected in a score but at the lowest end on account of there being no remedy.

  9. Once identified, each of these three severity bands must be treated by the system differently, as follows:

| Severity band | Severity score |
| --- | --- |
| No Remedy | 0.50 |
| Non-pecuniary | 0.30 |
| Fee remedy | 0.60 |
| Financial compensation | 1.00 |

  10. Each remedy must be assigned a base severity score according to its classification. This base score reflects the nature of the remedy only and must be applied to the score arising from the Remedy Amount.

  11. The second step is to assess **Remedy Amount**. This data is provided in a separate field within the LeO dataset. Bands already exist in the data and can be attributed scores as follows:

| Bands | Remedy Amount Score |
| --- | --- |
| £0 | 10 |
| £1–£299 | 12 |
| £300–£749 | 15 |
| £750–£999 | 17 |
| £1,000–£4,999 | 22 |
| £5,000–£9,999 | 26 |
| £10,000–£14,999 | 30 |
| £15,000–£19,999 | 34 |
| £20,000–£24,999 | 38 |
| £25,000–£29,999 | 42 |
| £30,000–£34,999 | 46 |
| £35,000–£39,999 | 50 |
| £40,000–£44,999 | 54 |
| £45,000–£49,999 | 58 |
| £50,000+ | 62 |

  12. Note that within the LeO data “N/A” appears in the Remedy Amount field. This is irrelevant because this corresponds only to those decisions where no poor service is found. Those decisions are excluded from the ranking logic.

  13. The third step is to factor in any **complaints handling** that is judged by LeO to have been unreasonable. This is a fixed penalty that is added to the score produced by combining Remedy Type and Amount.

  14. The fixed penalty for unreasonable complaints handling is **4**.

  15. If there is no finding of unreasonable complaints handling then no fixed score is added.

  16. Adding these three steps together, the formula is as follows:

| Deduction (per decision) = | (Severity score × Remedy Amount score)   + Complaint handling penalty |
| --- | --- |

  17. Each LeO decision is scored separately using the single-decision formula above. Where a firm has more than one in-scope decision, the total Complaints History deduction is the sum of those individual decision scores.

  18. The resulting figure is then deducted from base 100 to produce the Complaints History score that is taken into account in the relevant scorecard.
**Implementation**

  1. LeO decisions are linked to CML firm records through a one-time entity resolution process based on published provider name. Each matched record is then anchored to the LeO unique decision identifier (e.g. D011241), allowing all subsequent data handling to rely on that identifier rather than repeated name matching.

  2. CML maintains an internal mapping between LeO provider names and CML firm records, supported by standardised name normalisation and approved aliases where necessary.

  3. Once established, this mapping ensures that LeO data is deterministically reconciled via the LeO identifier, while SRA data continues to be reconciled via SRA ID, preserving consistency and auditability across both datasets.

**Visual representation**

  1. In the search results Complaints History is presented as a structured summary derived from LeO data. At search results level, the interface displays four items:

    1. A standardised visual severity indicator derived from the underlying score that is calculated as above. That score is standardised into the visual severity indicator as follows:

| Complaints History score | Display band | Visual (stars) |
| --- | --- | --- |
| 100 | No complaints history | 5/5 |
| 80–99 | Very low | 4/5 |
| 60–79 | Low | 3/5 |
| 40–59 | Moderate | 2/5 |
| 20–39 | Elevated | 1/5 |
| <20 | High | 0/5 |

    2. The number of in-scope LeO decisions currently published and over how long (usually 12 months): *“2 decisions (last 12 months)”*.

    3. The upheld complaint types, derived directly from the published data. No narrative or qualitative interpretation is applied.

    4. Users are provided with a direct link to the relevant Legal Ombudsman source to review the underlying decisions in full.

***Example (search result card):***

**Complaints history**●●○○○ Moderate
**3 decisions (last 12 months)**

**Common issues:**Delay · Failure to release files or papers · Poor communication

[View Legal Ombudsman decisions ↗]

## Factor 4: Regulatory History

1. This factor reflects publicly available regulatory history as a quality and trust signal.

2. The system must incorporate regulatory data published by the **Solicitors Regulation Authority** (the regulator of solicitors and law firms, “**SRA**”).

3. The treatment of regulatory data within the system must adhere to the following principles:

  1. **Firm-level assessment** - Regulatory history must be assessed at firm level only, with all relevant regulatory data aggregated to the firm entity and no distinction made between individual practitioners or office locations.

  2. **Source-based inclusion** - Only regulatory decisions that are actively published by the SRA may be included in the system. Where a regulatory decision is no longer published, it must be excluded from the system and must not influence ranking outcomes.

  3. **No editorial judgment** - The system may classify and structure regulatory data using predefined, rules-based categories, but must not apply subjective or qualitative judgment. It must only reflect observable outcomes as published by the relevant source.

  4. **No inferred or constructed data** - The system must not infer, estimate, or construct additional context beyond what is published by the SRA.

  5. **Downside-only signal** - Regulatory history must operate as a negative factor within the ranking model. The absence of adverse regulatory decisions must not result in a positive uplift in score.

  6. **Transparency and traceability** - All regulatory signals presented within the system must be traceable to their original source. Users must be provided with direct access to the relevant published material to enable further investigation.

  7. **Publication-based recency** - The inclusion of regulatory history is determined by their current publication status. No additional time-based weighting is applied beyond the publication policies of the SRA.

**Proposed MVP framework**

  1. The ranking principles applicable are as follows:

    1. The regulatory score must be constructed as an absolute score with a maximum value of 100, awarded to firms with no currently published regulatory findings. It should not be normalised in the manner other choice factors are.

    2. All currently published regulatory outcomes must reduce this score according to predefined severity-based deductions (see below).

    3. Reductions must increase non-linearly with outcome severity, such that more serious outcomes exert a disproportionately greater impact.

    4. Where multiple outcomes exist, all must be aggregated without adjustment for repetition or linkage.

    5. No minimum score is imposed. It is therefore possible for a regulatory score to be less than zero.

**SRA published outcomes**

  1. Regulatory outcomes published by the SRA must be incorporated as the primary source of firm-level regulatory data and they must be processed according to the nature of the outcome.

  2. The SRA publishes all decisions against SRA-regulated firms, including decisions made by the SRA itself under its own enforcement powers and also those determined by the independent Solicitors Disciplinary Tribunal (**SDT**).

  3. SRA and SDT decisions are made according to different sanctions guidance and therefore must be assessed differently for the CML ranking logic, as follows.

**SRA decisions**

  1. The SRA can rebuke a firm, fine it or control it through conditions on its practicing licence or by closing it down altogether (an intervention).

  2. Each decision type must be classified into the following categories for the purposes of the model:

    1. **Rebuke** - A formal finding of misconduct without financial penalty. The entry point for SRA sanctions.

    2. **Fixed Financial Penalty** - Financial penalties imposed at a fixed level for lower-level regulatory breaches.

    3. **Financial Penalty (Banded)** - Financial penalties imposed under the SRA’s penalty band framework, classified according to the published bands (Bands A to D). If the band is expressed within the published decision (as is usually the case) then that band is determinative of seriousness. If no band is expressed it must not be inferred and instead that fine is attributed to a distinct category within the model.

    4. **Conditions** - Regulatory conditions imposed on a firm’s authorisation, reflecting ongoing regulatory control or restriction. Conditions imposed by the SRA must be treated as a single category and must not be sub-classified or graded. The existence of conditions reflects ongoing regulatory control and must be positioned within the severity hierarchy above financial penalties Band B but below Band C.

    5. **Intervention** - Regulatory intervention into a firm’s practice, representing the most serious form of regulatory action. The SRA shuts the practice down, with little hope of it being revived. The ranking logic should use an intervention decision as a binary eligibility condition rather than a scoring factor. *Any such firm should be removed from the results set entirely.*

  3. The following deduction values must apply to SRA outcomes:

| SRA decision type | Deduction value | Resulting Regulatory History score (from base 100) |
| --- | --- | --- |
| Rebuke | -5 | 95 |
| Fixed financial penalty | -6 | 94 |
| Financial penalty (band A) | -10 | 90 |
| Financial penalty (unbanded) | -12 | 88 |
| Financial penalty (band B) | -15 | 85 |
| Conditions | -25 | 75 |
| Financial penalty (band C) | -40 | 60 |
| Financial penalty (band D) | -60 | 40 |

  4. These deduction values must be applied cumulatively to the base score of 100 in accordance with the aggregation principles set out above (see 8.4.4).

  5. Financial penalties must be classified by reference to the published SRA penalty band where expressly stated. Where no penalty band is specified, the penalty must be treated as an unbanded financial penalty.

  6. Conditions must be treated as a single category and must not be sub-classified or graded.

  7. The application of the above deductions must reflect the relative severity hierarchy of SRA outcomes, such that higher-severity outcomes produce disproportionately greater reductions in the regulatory score.

**SDT decisions**

  1. Financial penalties imposed by the SDT are published on the SRA website. They must be classified using a six-level severity structure aligned to the SRA financial penalty framework, adopting the following thresholds:

| SDT imposed fine | Deduction value | Resulting regulatory history score |
| --- | --- | --- |
| £0 – £10,000 | −10 | 90 |
| £10,001 – £25,000 | −15 | 85 |
| £25,001 – £75,000 | −25 | 75 |
| £75,001 – £200,000 | −40 | 60 |
| £200,001 – £500,000 | −50 | 50 |
| £500,001+ | −60 | 40 |

**Ingestion of SRA published outcomes**

  1. Regulatory history data from SRA and SDT outcomes must be taken from the decisions published by the SRA on its website, which includes SDT outcomes.

  2. The system must perform a daily scan of newly published regulatory decisions on the SRA website in order to identify and ingest new outcomes as they become available, relying on the unique SRA ID for each firm as the primary matching key to the CML database.

  3. The system must perform a full reconciliation scan of all recorded firms and associated regulatory outcomes at least once every seven days in order to:

    1. identify outcomes that have been removed from publication;

    2. identify outcomes that have been amended or replaced; and

    3. ensure that the dataset reflects the current published position.

  4. The inclusion of any regulatory outcome in the model must be strictly dependent on its current publication status. If an outcome is no longer published by the SRA, it must be removed from the dataset and must no longer contribute to the regulatory score.

  5. The system must not retain or rely upon historical regulatory data that is no longer publicly available from the source.

  6. Where a published outcome is updated (including as a result of appeal or revision), the system must reflect the updated published outcome and must not retain any superseded version.

**Visual representation**

  1. In the search results Regulatory History is presented as a structured summary derived from SRA data in a consistent format to the presentation of Complaints History. At search results level, the interface displays four items:

    1. A standardised banded indicator derived from the Regulatory History score:

| Regulatory History score | Display band | Visual (stars) |
| --- | --- | --- |
| 100 | No findings history | 5/5 |
| 80–99 | Very low | 4/5 |
| 60–79 | Low | 3/5 |
| 40–59 | Moderate | 2/5 |
| 20–39 | Elevated | 1/5 |
| <20 | High | 0/5 |

    2. The number of published outcomes;

    3. The outcome types (e.g. rebuke, financial penalty band, conditions), derived directly from SRA data without narrative or qualitative interpretation; and

    4. A direct link to the SRA source material to review the underlying decisions in full.

## Factor 5: Distance to closest office

1. This is the only optional choice factor, which users can elect to include or exclude from the ranking logic. For some users, they will be content to receive their legal services remotely and office proximity is not relevant.

2. If a user does not want to take into account office proximity, they are ranking according to five choice factors rather than the default six. Therefore, office proximity must be excluded from the scorecard. The weightings of the remaining factors must then be proportionately rescaled so that the total weighting across active factors equals 100. The relative proportions between the remaining factors must be preserved by proportionately rescaling their original weightings from the selected scorecard.

3. Alternatively, if a user enters their postcode during the intake to indicate they do want office proximity taken into account then the system behaves as follows:

  1. The system must maintain a dataset of office locations for each firm.

  2. For the purposes of the pilot, this dataset may include:

    1. the primary office address obtained from regulatory data; and

    2. any additional office locations identified and recorded by CML.

  3. Where multiple office locations exist for a firm, all recorded office locations must be considered in the distance calculation.

  4. Distance must be calculated by reference to the nearest recorded office location of the firm to the user’s relevant location. It is calculated as straight-line (geodesic) distance between the user’s postcode location and the relevant office postcode location.

  5. The nearest office must be determined solely by geographic proximity and must not take into account internal firm structure, staffing, or service allocation across offices. For the purposes of the pilot, all recorded office locations of a firm are treated as capable of delivering the defined legal service.

  6. This assumption reflects the practical reality that legal services are frequently delivered across offices and are not confined to a single physical location.

  7. Accordingly, distance is intended to represent user accessibility to the firm, rather than the specific location at which legal work is performed.

  8. This assumption may be refined in future iterations (post pilot) where firm-specific service capability data becomes available.

  9. Closer firms should score more highly in a normalised distance score, calculated as follows:

| Normalised Distance Score | = | (Dmax – Dfirm) | x 100 |
| --- | --- | --- | --- |
|  |  | (Dmax – Dmin) |  |

4. As per the logic treatment of all other choice factors, tie breakers are not required at choice factor level and a normalised distance score of 50 is assigned to all firms in the unlikely event *D*max = *D*min.

## Factor 6: Number of offices

1. This factor is a light indicator of operational scale and physical coverage.

2. It is intentionally weighted lowest so that it informs ranking without dominating it.

3. The system must use the total number of offices recorded for the firm.

4. The number of offices is incorporated as a structured indicator of firm scale. Firms are assigned to predefined bands based on the number of office locations, with scores increasing in a bounded, non-linear manner to reflect diminishing incremental value from additional offices. The scoring model saturates at higher office counts to avoid disproportionate advantage for large firms. No geographic weighting or qualitative assessment of office location is applied within this factor, as follows:

| Offices | Score |
| --- | --- |
| 1 | 70 |
| 2–3 | 78 |
| 4–6 | 85 |
| 7–10 | 90 |
| 11–20 | 95 |
| 21+ | 100 |

5. This is visually represented in the score card as the number of offices and no more: *“2 offices”*.

## Final ranking score

1. The overall ranking score is calculated as a weighted sum of the individual choice factor scores, with each factor contributing in accordance with its predefined weighting.

2. The weightings applied are determined by the selected scorecard, with the underlying factor scores remaining unchanged across all scorecards.

3. Firms are then ranked from highest to lowest, with their overall scores displayed as an integer on the far right of the search results.

## Tie handling

1. If two firms receive the same final ranking score on a full numerical precision basis (in the backend), the system must apply a fixed tie break order.

2. Proposed tie break order:

  1. Higher Reputation score;

  2. Higher Complaints History score;

  3. Higher Regulatory History score;

  4. Higher price score;

  5. Shorter distance to nearest office;

  6. Higher number of offices; then

  7. Alphabetical by firm name (final fallback only).

3. This ensures deterministic ordering even where firms are otherwise tied.

## Sort functionality in full results

1. The full market results must also allow the user to sort by individual factors.

2. This sort function is a display tool only. It does not alter the underlying default ranking methodology.

3. It is not required in the top five results, appearing above the full set.

## Data requirements

1. The ranking engine requires structured inputs for each firm as follows:
  1. firm identifier

  2. quoted price for the specific search
  3. average review rating
  4. review count
  5. complaints history score
  6. regulatory history score
  7. nearest office distance
  8. office count
2. These values must be available in structured form at runtime.

3. All interpretation, cleansing, normalisation, scoring, and categorisation of underlying source data must be completed prior to runtime, such that the ranking engine operates solely on pre-processed, deterministic inputs.

## Auditability and explainability

1. The ranking model must be capable of explanation at both system and firm level.

2. At minimum, the system should allow CML internally to identify for any given search:

  1. each raw factor input used

  2. each normalised factor score

  3. the weighted contribution of each factor

  4. the final score

  5. the reason one firm ranked above another

3. This is necessary for trust, debugging, refinement and future investor diligence.

## Prioritised Scorecard Methodology

1. Providing guided user autonomy is essential to building trust in the brand and in achieving the long-term value of CML.

2. If a user does not want to adopt the default balanced scorecard approach to ranking firms they can specify a prioritised scorecard instead. This is done immediately before search results are generated.

3. The prioritised scorecard builds on the default balanced scorecard by allowing the user to increase the importance of a single chosen factor, while preserving the overall structure of the ranking model. If the user confirms that they want to use the prioritised scorecard then each choice factor is presented as an option for the user to click on. They can only click on one. That factor is then given greater weighting within the scorecard, and the remaining factors are proportionally reduced but retain their original relative order and influence as per the balanced scorecard. This ensures that user preferences are reflected in the ranking, while maintaining a consistent, deterministic and balanced assessment across all relevant factors.

4. The structure remains the same between balanced and prioritised scorecards but users have the autonomy to express which factor matters most to them, if they want to.

5. As a very important aside, two significant secondary consequences flow from building in some user autonomy:

  1. First, this functionality will give far greater insights into consumer behaviours at the point of purchasing legal services. Those insights are valuable and sought-after, and therefore monetisable.

  2. Second, the natural consequence of allowing users to specify a priority choice factor will be variations in rankings. This produces a greater spread of firms appearing at the top end of the results and therefore a wider distribution of instructions than a single ranking logic.

6. Each prioritised scorecard applies a predefined set of weightings as set out on the next page. The default balanced scorecard is applied unless the user selects a priority factor, in which case the corresponding weighting set is applied.

|  | PRIORITISED SCORECARDS |
| --- | --- |
| Factor | Balanced Scorecard (Default) | Reputation Priority | Cost Priority | Complaints Priority | Distance Priority | Regulatory Priority | Number of Offices Priority |
| Reputation | 25 | 40 | 20 | 18 | 17 | 18 | 17 |
| Cost | 25 | 20 | 40 | 18 | 17 | 18 | 17 |
| Complaints | 15 | 12 | 12 | 40 | 10 | 10 | 10 |
| Regulatory | 15 | 12 | 12 | 10 | 10 | 40 | 10 |
| Distance | 10 | 8 | 8 | 7 | 40 | 7 | 6 |
| Number of Offices | 10 | 8 | 8 | 7 | 6 | 7 | 40 |
| Total | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

7. For transparency in relation to calculating the prioritised scorecard weightings:

  1. The selected priority factor is weighted as 40 to provide clear dominance;

  2. The ordering of the remaining factors follows the order from the balanced scorecard;

  3. The remaining factors share the balance of 60 proportionally, preserving their original relative weightings from the balanced scorecard (but reduced to reflect the aggregate value of 60 rather than 75 or more); and

  4. All weightings are expressed as integers for implementation simplicity.
