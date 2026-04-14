# Contributing to HIL Venue Tracker

This project is maintained by the HIL lab. The most valuable contributions are keeping conference dates accurate and filling in missing details in venue notes files. All data lives in plain text files — no special tooling required to contribute.

## How to contribute

1. Fork or create a branch from `main`.
2. Make your changes (see sections below).
3. Run `python timeline_generator.py` locally to confirm the plot renders correctly.
4. Open a pull request with a brief description of what changed and why.

---

## Updating existing dates

Conference dates shift by a few days each year. Before a submission season, check each venue's CFP page and update `conferences.csv`:

1. Find the venue's current CFP page (the `url` column is a starting point).
2. Update `month`, `day`, and `year_offset` for all affected rows of that venue.
3. Update `url` if the CFP page has changed.
4. Remove `Approximate dates; verify for current year` from the `notes` field once real dates are confirmed.

Run `python report.py --approx` to get a quick list of venues that still have approximate dates.

Do **not** change `BASE_YEAR` in `timeline_generator.py` as part of a routine date update — coordinate with the lab before doing the annual year rollover.

---

## Adding a new venue

### 1. Add rows to `conferences.csv`

Add one row per event (one for the conference date, one per deadline):

```
MYVENUE,Full Conference Name,true,top,conference,5,20,0,https://cfp-url.com,,notes/MYVENUE.md,~20%
MYVENUE,Full Conference Name,true,top,deadline,10,15,-1,https://cfp-url.com,,notes/MYVENUE.md,~20%
```

**Field guidance:**

| Field | Guidance |
|-------|----------|
| `tier1` | `true` for tier-1 or broadly reputable HPC venues. When in doubt use `false` — it can be promoted later. |
| `tier` | `top` for SC/IPDPS/PPoPP-level venues; `regular` for reputable but not top-tier; `workshop` for co-located workshops. |
| `year_offset` | `0` for events in `BASE_YEAR`; `-1` for events in the prior calendar year (e.g. an October deadline before a February conference). |
| `notes` | One-liner flag only. Notes ≤14 characters appear as labels on the timeline plot (e.g. `Cycle 1`, `Round 2`). Avoid commas; use semicolons. |
| `notes_file` | Relative path to the venue's markdown file, e.g. `notes/MYVENUE.md`. Use the same value on every row for that venue. |
| `url` | Link to the current CFP page. Update this each year. |
| `acceptance_rate` | Approximate historical rate, e.g. `~20%`. Leave blank if unknown. This is stable year-to-year so only needs updating if the venue's selectivity changes significantly. |

### 2. Create a notes file

Copy [`notes/TEMPLATE.md`](notes/TEMPLATE.md) to `notes/MYVENUE.md` and fill in what you know. Leave sections blank rather than omitting them — blank sections signal to future contributors what still needs research. Good things to document:

- Submission format (page limit, blind review type, LaTeX template)
- Review process (number of reviewers, rebuttal, revision cycles)
- Lab tips (travel grants, student volunteer opportunities, co-located events)

### Tier classification

| `tier` value | Meaning |
|---|---|
| `top` | Premier HPC venue (SC / IPDPS / PPoPP / ASPLOS / HPCA level) |
| `regular` | Reputable but not the highest tier |
| `workshop` | Co-located workshop |

`tier1` controls whether a venue appears in the default view, independently of `tier`. A `regular` conference can be `tier1=true` if the lab actively targets it.

---

## Removing a venue

Do not delete rows. Set `tier1=false` and add a short note explaining why (e.g. `not HPC-focused`). This keeps historical context and lets anyone see the full picture with `--show-all`.

---

## Updating venue notes

Long-form notes live in `notes/<VENUE>.md`. These are free-form markdown — edit them directly. Useful things to add or update:

- Confirmed acceptance rates (update both the notes file and the `acceptance_rate` column in the CSV)
- Review process details from experience submitting to the venue
- Changes to submission format or page limits
- Travel grant deadlines and application links

---

## Data format rules

- **No commas in any CSV field** — use semicolons in `notes`, `full_name`, etc.
- **One `conference` row per venue** — each venue must have exactly one row with `event_type=conference`. Multiple `deadline` rows are allowed.
- **Approximate dates** — if only an estimate is available, add `Approximate dates; verify for current year` to the `notes` field. This surfaces the venue in `python report.py --approx`.
- **Same metadata on every row** — fields like `full_name`, `tier1`, `tier`, `url`, `notes_file`, and `acceptance_rate` should have the same value on every row for a venue (they are venue-level, not event-level).

---

## What not to commit

- `targets.csv` entries for your own papers — this file is for personal use and should stay local (it is gitignored by convention).
- Generated output files (`conference_timeline.png`, `deadlines.ics`) — these are regenerated automatically by the GitHub Actions workflow when `conferences.csv` changes.
