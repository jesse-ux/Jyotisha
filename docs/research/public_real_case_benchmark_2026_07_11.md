# Public Real-Case Jyotish Benchmark - 2026-07-11

## Result

Ten public cases with Astro-Databank Rodden `A/AA` birth times were replayed through the local evidence stack. No user birth data or private feedback was used.

| Metric | Result | Boundary |
|---|---:|---|
| Cases / dated events | 10 / 10 | 5 career, 5 marriage |
| Positive-event activation recall | 80% | 8 of 10 known events reached weak or strong activation |
| Strong hits | 30% | 3 of 10 |
| Exact-label rate | 30% | Weak domain activation is not exact event classification |
| Blocked local replays | 0% | All lightweight local evidence packets completed |
| Balanced accuracy / specificity | blocked | No independently verified negative-control dates |

This is not scientific predictive accuracy. It is a positive-event technical activation replay. Full machine output: [`docs/benchmark/public_real_case_benchmark_2026_07_11.json`](../benchmark/public_real_case_benchmark_2026_07_11.json).

## Cases

| Case | Event | Domain | Rodden | Result | Score |
|---|---|---|---|---|---:|
| Steve Jobs | iPhone introduction, 2007-01-09 | career | AA | weak | 5 |
| Barack Obama | presidential election, 2008-11-04 | career | AA | miss | 1 |
| Arnold Schwarzenegger | California recall election, 2003-10-07 | career | A | miss | 2 |
| Meryl Streep | Best Actress Oscar, 1983-04-11 | career | AA | weak | 5 |
| Jennifer Aniston | lead-actress Emmy, 2002-09-22 | career | AA | weak | 5 |
| Prince William | legal marriage, 2011-04-29 | marriage | AA | weak | 6 |
| Angelina Jolie | legal marriage, 2014-08-23 | marriage | AA | weak | 4 |
| Frida Kahlo | legal marriage, 1929-08-21 | marriage | AA | strong | 7 |
| Snoop Dogg | legal marriage, 1997-06-14 | marriage | AA | strong | 10 |
| Walt Disney | legal marriage, 1925-07-13 | marriage | A | strong | 8 |

## Sources

Birth times: [Jobs](https://www.astro.com/adbvip/adbvip_02_24.htm), [Obama](https://www.astro.com/adbvip/adbvip_08_04.htm), [Schwarzenegger](https://www.astro.com/adbvip/adbvip_07_30.htm), [Streep](https://www.astro.com/adbvip/adbvip_06_22.htm), [Aniston](https://www.astro.com/adbvip/adbvip_02_11.htm), [Prince William](https://www.astro.com/adbvip/adbvip_06_21.htm), [Jolie](https://www.astro.com/adbvip/adbvip_06_04.htm), [Kahlo](https://www.astro.com/adbvip/adbvip_07_06.htm), [Snoop Dogg](https://www.astro.com/adbvip/adbvip_10_20.htm), [Disney](https://www.astro.com/adbvip/adbvip_12_05.htm).

Event dates: [Apple Newsroom](https://www.apple.com/newsroom/2007/01/09Apple-Reinvents-the-Phone-with-iPhone/), [FEC Federal Elections 2008](https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/federal-elections-2008/), [California Secretary of State](https://elections.cdn.sos.ca.gov/sov/2003-special/sov-complete.pdf), [Oscars 1983](https://www.oscars.org/oscars/ceremonies/1983), [Television Academy 2002](https://www.televisionacademy.com/awards/nominees-winners/2002/outstanding-lead-actress-in-a-comedy-series), [Royal Family wedding record](https://www.royal.uk/wedding-prince-william-and-miss-catherine-middleton), [Angelina Jolie biography](https://en.wikipedia.org/wiki/Angelina_Jolie), [Frida Kahlo biography](https://en.wikipedia.org/wiki/Frida_Kahlo), [Snoop Dogg biography](https://en.wikipedia.org/wiki/Snoop_Dogg), [Walt Disney Family Museum](https://www.waltdisney.org/blog/who-did-walt-disney-marry).

## Pre-Registered Replay Logic

- D1 event-house ownership and occupation.
- D10 for career; D9 for marriage.
- A10 for career; UL for marriage.
- Functional Benefic/Malefic by Lagna.
- Vimshottari Mahadasha and Antardasha at the event date.
- Narayana Dasha at event age.
- Jupiter-Saturn Double Transit PAC for house 10 or 7.

Thresholds were frozen before the batch run: `>=7 strong`, `4-6 weak`, `<4 miss`.

## Findings

1. Marriage timing is stronger in this sample: `5/5` activation recall, including three strong hits.
2. Career timing is weaker: `3/5` activation recall and no strong hit. Public-office elevation is not captured well by direct 10/6/9/11 ownership alone.
3. General missing career layers: D10 Lagna/10L hierarchy, A10 sign activation, Amatyakaraka, Raja-yoga activation, Rahu/Ketu dispositor results, and Varshaphala/Tajika annual confirmation.
4. Double Transit is confirmation, not a standalone verdict.
5. `80%` must not be advertised as predictive accuracy: five hits are weak, exact-label rate is `30%`, and no negative controls were tested.
6. Do not tune thresholds on these same ten cases. Freeze v2 rules, then validate on a new holdout batch.

## Technique Audit

| Technique | Status | Notes |
|---|---|---|
| D1 | used | All 10 cases |
| D9 / D10 | used | Domain-specific |
| UL / A10 | used | Lord linkage included |
| Functional Benefic/Malefic | used | Lagna-specific roles retained |
| Vimshottari MD/AD | used | Event-date boundaries |
| Narayana Dasha | used | Event-age sign/lord |
| Double Transit PAC | used | House 7 or 10 |
| MEVG / Global Web Evidence | used | Astro-Databank plus independent event sources |
| Real Case Calibration | used | 10 structured cases; positive events only |
| VedAstro official raw | blocked | `official_snapshot_budget_exhausted` |
| PyJHora / JHora parity | blocked | Missing canonical fixture; JHora automation absent |
| jyotishganit | partial | Importable readiness only; not event-timing oracle |

## Next Holdout Design

- Add 10 new cases not used here: 5 public-status career events and 5 marriages.
- Add sourced negative-control windows to estimate specificity and balanced accuracy.
- Freeze v2 career rules before holdout: node dispositor, D10 10L, A10 transit/dasha, AmK, Raja yoga, annual chart.
- Keep v1 and v2 reports side by side; reject rules that improve training cases but fail holdout.
