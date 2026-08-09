VOTE: REJECT

Two concrete amendments would flip me to APPROVE:

1. **Fix the validation contradiction.** Leave-one-episode-out is not walk-forward because a held-out historical episode is predicted using later episodes. It violates the no-look-ahead constraint and cannot be the primary metric. Replace Section 6 with:
   - Primary: **expanding-origin walk-forward**, with all observations whose 12-month target windows overlap the test episode purged from training.
   - Episode bootstrap or LOEO may be reported only as sensitivity/stability analyses, never as walk-forward skill.
   - Hyperparameter and feature selection must occur entirely inside each historical training window.

2. **Define the NBER target and label availability precisely.**
   - Use **recession onset**, not “any recession month,” otherwise long recessions create positive targets after onset and the model partly predicts continuation rather than entry.
   - Define \(Y_t=1\) when an NBER recession onset falls in months \(t+1,\ldots,t+12\).
   - At each historical refit date, include a training label only if its complete 12-month horizon has elapsed **and** the relevant NBER peak/trough status was publicly declared by that date. Use a small committed table of NBER announcement dates; current USREC values alone are not real-time labels.
   - Replace the arbitrary six-quarter embargo with this information-date rule. A conservative fixed embargo may be an operational fallback, but it must be demonstrated to cover the historical maximum declaration lag.

Reservations otherwise: preregister the numerical monthly non-inferiority margin, and do not print a probability ratio when the base-rate sensitivity band is broad enough to make that ratio misleading.