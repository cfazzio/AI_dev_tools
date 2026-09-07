# Care Log — Project Plan

A tool for tracking time, mileage, and tasks related to caring for an aging parent
in assisted living with a progressive disease.

**Status:** scope agreed. Spec not yet written.
**Date:** September 7, 2026

---

## 1. The problem

Caring for a parent in assisted living generates three streams of work that are easy to
lose track of and expensive to lose track of:

- **Time** — visits, phone calls, paperwork, coordination.
- **Mileage** — repeated drives to the facility, doctors, pharmacy.
- **Tasks** — recurring care obligations, questions to raise at the next visit, follow-ups
  from calls.

Two payoffs. Day to day, nothing falls through. Once a year, the mileage and out-of-pocket
totals are already assembled for taxes instead of being reconstructed from memory and
credit card statements.

The disease is progressive, so the load grows. A record that spans years is worth more
than a record that spans a month.

---

## 2. Decisions made

Each row closed a fork. The right-hand column is what the decision rules out — kept
deliberately, because it's the part that's easy to forget and expensive to reopen later.

| Question | Decision | What this rules out |
|---|---|---|
| Who uses it? | **One user.** Just me. | Sharing, permissions, attribution, edit conflicts, "who logged this" |
| What does it produce? | **Real-time capture, plus month-end and year-end numbers.** | A purely retrospective shoebox; a purely forward-looking to-do app |
| How is a visit captured? | **Start/stop timer, every entry editable after.** | Pure retroactive entry; a timer that assumes you never forget |
| Where do miles come from? | **Saved routes, with odometer override.** | Typing miles every time; GPS tracking |
| What lands on the task list? | **Recurring care calendar · agenda for next visit · follow-ups from calls.** | Open-ended decisions with no due date ("is it time for memory care?") |
| What's the deliverable? | **Spec first, then build.** | Building straight to code |

### On the timer choice

"Real time" was the operative phrase. It changes the tool from a data-entry form into a
capture device, and it has a side benefit worth naming in the spec: a contemporaneous
record — written as it happens — is the kind that holds up if the mileage log is ever
questioned. A log reconstructed in April is weaker evidence than one written in the
parking lot.

### On saved routes

The 90% case is the same few destinations over and over: the facility, the doctor, the
pharmacy. Defining "Home → [Facility], 14.2 mi round trip" once turns a trip into two
taps. Friction is what kills a log kept by an exhausted person, so this is the single
highest-leverage design decision in the tool.

The odometer override exists for the other 10% — a hospital run, an unusual detour —
where a real reading is both more accurate and better documentation.

---

## 3. In scope

**Capture**

- Start/stop timer for a visit or task session
- Route picker at start; miles prefill from the saved route
- Odometer in/out as a per-trip override
- Every entry editable after the fact
- Non-driving time entries (phone calls, paperwork, insurance, coordination)
- Out-of-pocket expenses, with a category and a deductible flag

**Tasks**

- Recurring care calendar: prescription refills, facility invoice review, care plan
  meetings, Medicare open enrollment, insurance renewals
- Agenda for next visit — items surfaced *when the timer starts*, so they don't evaporate
  the moment you walk in
- Follow-ups from phone calls: deadline plus a note recording who said what, and when

**Numbers**

- Month-end: hours, miles, out-of-pocket
- Year-end: deductible miles × the correct IRS medical rate, hours total, out-of-pocket total
- Export

---

## 4. Out of scope

Cut deliberately. Each is defensible on its own and each would double the project.

| Cut | Why |
|---|---|
| Care journal / symptom notes | A different kind of record with different privacy weight. Worth building; not this. |
| Medication list | Real value, but it's a clinical safety tool and wrong to half-build. |
| Document storage | Turns a tracker into a filing cabinet. |
| Multi-user / sibling access | Ruled out at the first fork. Reopening it changes the data model. |
| GPS mileage tracking | Unreliable in a web page, battery-hungry, needs the screen awake, may not be permitted. Saved routes get most of the benefit for none of the risk. |

---

## 5. Design problems the spec has to solve

These are the three places where a naive build would be wrong. They're also the most
defensible things to write about, if the work is being graded.

### 5.1 Not all the miles are deductible

A trip taken **to obtain medical care** is a deductible medical expense. A social visit
is not, even though it's the same drive to the same building. The tool cannot assume, so
it has to ask per trip — ideally as a default inferred from the trip's purpose, which the
user can correct.

The spec should state plainly that this is a record-keeping aid, not tax advice, and that
the deductibility call is the user's (or their accountant's). Two further constraints
worth naming: medical expenses are only deductible above 7.5% of adjusted gross income,
and only for a taxpayer who itemizes — so the tool's year-end number is an *input* to that
calculation, not the deduction itself.

### 5.2 The 2026 rate changed mid-year

The IRS medical mileage rate is not one number for 2026:

| Period | Rate |
|---|---|
| Jan 1 – Jun 30, 2026 | 20.5¢ / mile |
| Jul 1 – Dec 31, 2026 | 23.5¢ / mile |
| 2025 (full year) | 21¢ / mile |

A tool that applies a single flat rate to the year produces a wrong number. The rate must
be a function of the trip date, and the rate table must be visible and editable so the
tool doesn't silently go stale in 2027.

### 5.3 The timer will get left running

This is the central design problem, not an edge case. On the hard days — the ones that
generate the most billable-feeling hours — the person is least likely to remember to stop
a timer.

Proposed rule, to be pinned down in the spec: a session running past a threshold prompts
on next open, offering a best guess rather than a blank field — *"Still at the visit, or
did this end around 3pm?"* Never silently bank a fourteen-hour visit; never silently
discard one either.

---

## 6. Reference data

**IRS standard mileage rate, medical purposes**

- 2025: 21¢ per mile
- 2026, Jan 1 – Jun 30: 20.5¢ per mile
- 2026, Jul 1 – Dec 31: 23.5¢ per mile (raised mid-year on fuel costs)

**Medical expense deduction**

- Deductible only to the extent total qualified medical expenses exceed 7.5% of AGI
- Requires itemizing on Schedule A
- Assisted living costs may be partly or wholly qualifying depending on whether the care
  is medically necessary and certified — a question for a tax professional, not this tool

Sources:
[IRS 2026 standard mileage rates](https://www.irs.gov/newsroom/irs-sets-2026-business-standard-mileage-rate-at-725-cents-per-mile-up-25-cents) ·
[Mid-year rate increase, July 2026](https://www.journalofaccountancy.com/news/2026/jul/irs-raises-standard-mileage-rates-for-remainder-of-2026/)

---

## 7. Open question

**Does the spec argue its tradeoffs, or just specify the build?**

- If it's graded on *design thinking*: write the rejected alternatives in — GPS, retroactive
  entry, multi-user — with the reasoning that killed each one. Section 2's right-hand
  column becomes a full section.
- If it's graded on *clarity of the build*: that's noise. Cut to data model, screens, and
  behavior.

---

## 8. Next step

Write the spec: user stories, data model, screen-by-screen behavior, and the three design
problems in section 5 resolved into actual rules. Then build to it.
