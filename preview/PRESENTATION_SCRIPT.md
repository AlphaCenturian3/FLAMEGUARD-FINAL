# Four-minute judge presentation script

Spoken text is in quotation marks; **Do** lines say what to click. Fixture means invented placeholder data. Nothing here is a NASA measurement, and nothing is a validated conclusion. Keep `preview/LAUNCH_CARD.md` open for the addresses.

## 0:00 to 0:30 — Problem and mission
"Without gravity, flames behave differently, and fire is among the most serious risks on a spacecraft, a station, or a Moon or Mars habitat. NASA has run microgravity combustion experiments, but the results sit in long reports. FlameGuard-SI makes that evidence searchable and traceable: what NASA reported, where, and what we are not sure about."
**Do:** show the live address, http://127.0.0.1:8790/.

## 0:30 to 1:15 — Evidence Explorer and the provenance architecture
"This is the live system. It says zero investigations loaded, and that is on purpose. Every value has to carry its source, its page and its exact quote, and it has to pass automatic checks: file fingerprints, schema, and provenance. If a file fails, the system withholds it and tells you, instead of guessing. We have prepared NASA's FLEX droplet-combustion table and audited it against the original report, but we are holding it back until independent scientific review is finished. So today the live explorer is honestly empty, the ranking page says it is not implemented, and nothing is invented to fill the gap."
**Do:** click **Evidence Explorer** ("No investigations available"), then **Rank** ("HTTP 501").

## 1:15 to 2:15 — Guided fixture demonstration and the exclusion safeguard
"To show how it will look, here is fixture mode. Every page carries this banner: fixture data, not NASA data. These records are invented placeholders. Here is a safeguard we care about: when a source number conflicts with its own figure caption, we do not quietly use it, and we do not quietly delete it. We mark it excluded, show the reason and the source quote, and never display the number. Anything built on an excluded value can only explain the exclusion; it can never feed a ranking, a comparison or an answer."
**Do:** open http://127.0.0.1:8790/?fixtures=1, read the banner, open **Evidence Explorer**, scroll to the excluded finding, already open on the page ("Excluded by FlameGuard-SI", "value not shown"). Go back to **Overview**, click **Start 90-second demo** and press **Next** through the five steps: Discover, Compare, Rank, Interpret, Safety Insight.
**If asked about the ranking shown in fixture mode:** "That ranking is a placeholder. The live backend returns not-implemented for rankings until approved evidence exists."

## 2:15 to 3:00 — Interpretation and fire-safety relevance
"The interpretation page is where evidence becomes fire-safety insight, for example for a lunar base. What you see here is a placeholder example of the format, not a validated conclusion. Notice the rules: an interpretation must list the measured records it came from, it is labelled as our analysis and not a NASA statement, it states its limitations, such as tested conditions differing from lunar gravity, and the page says we do not extrapolate to conditions that were not tested. Our goal is to help researchers ask better questions, not to issue safety ratings."
**Do:** on **Interpret & Insight** choose **Lunar base** in the Application context list; point at the label "Not a NASA statement" and the limitation text.

## 3:00 to 3:40 — Blender gravity visualisations and their limits
"These four images show the same small flame under Earth, Mars, Moon and microgravity conditions. They are artistic illustrations. The shape change is a design choice to show the idea that buoyancy weakens as gravity drops; it is not a simulation, it is not validated, and it is not NASA data. Fuel, oxygen, pressure and airflow are not modelled. Every image says so on its face, and I will read it: illustration only, not a validated combustion simulation, not NASA data."
**Do:** open http://127.0.0.1:8790/illustrations/ (earth, mars, moon, microgravity). Read the printed disclaimer once: **ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.**

## 3:40 to 4:00 — What is implemented, limits, closing
"Working today: the evidence explorer, fail-closed loading, honest empty states, exclusion safeguards and a guided tour. Not built yet: NASA findings in the app, real rankings and the assistant, which wait for independent review. We would rather show an empty page than an unverified number. FlameGuard-SI: every value shows where it came from."
**Do:** open **Overview** on the live address and stop there.

## Never say
Any FLEX or other NASA number; that fixtures are NASA data; that rankings, comparisons or the assistant work on real evidence; that the Blender images are simulations or predictions; that our tests or audits are a scientific approval.
