---
title: Destination Earth learning book and browser lab
type: feature
created: 2026-11-15
status: done
route: dispatch
review_loop_iteration: 0
context: []
baseline_commit: f1080aa5a336a9baa51d5b1fcbcc8ff031f54196
---

<frozen-after-approval reason="User requested complete repository implementation">

## Intent

Create an independent educational repository introducing Destination Earth with a polished README, original splash artwork, a Jupyter Book, and runnable JupyterLite notebooks. The same notebooks serve as book chapters. Readers can progress from architecture and data access to scientific analysis, maps, 3D scenes, globes, dashboards, and reproducible workflows.

## Boundaries & Constraints

Always use original explanations, original generated artwork and explicitly synthetic demonstration data. Attribute official conceptual sources, EU ownership and entrusted entities accurately. Keep authentic service access separate from browser demonstrations and document service-specific terms. Preserve dependency licenses. All notebooks must have a splash image in the first cell, objectives, substantive runnable exercises, checks, interpretation, and references.

The repository is educational, not an official service or full reimplementation of HPC models. Do not copy agency images, logos, external notebook code, observational datasets or model outputs. Do not request or embed credentials in the static site. Links to deployment destinations must be labeled pending until deployment is observed. Production service access, restricted data redistribution, and live simulation submission are not implied by browser exercises.

## I/O & Edge-Case Matrix

| Scenario | Input | Behavior | Handling |
|---|---|---|---|
| Fresh learner | Modern browser | Lab loads notebooks and runs synthetic examples | Explain first-run package downloads |
| No DestinE account | Default exercises | Complete synthetic path remains available | Link official registration and access policy |
| Official data | User-authorized small export | Validate schema, units, coordinates and provenance | Reject invalid input without synthetic fallback |
| Browser restrictions | Missing CORS/native libraries | Explain server-assisted route | Never expose secrets or pretend access succeeded |
| Unpublished repository | README launch links | Provide configured URLs and source links | Explicit pending-deployment status |

</frozen-after-approval>

## Code Map

The initial repository has only `README.md`; main starts at `f1080aa5a336a9baa51d5b1fcbcc8ff031f54196`. No application conventions or user modifications exist. `content/` will hold canonical notebooks and shared Python utilities. `myst.yml` will consume those notebooks directly. Build scripts stage the same files for JupyterLite and combine outputs into `_site/`. Root documentation contains provenance, operating instructions and citations. The build workflow's `_bmad/` runtime is local tooling, not published content.

## Tasks & Acceptance

**Execution:**
- [x] `content/` — implement at least twenty connected educational notebooks with a common helper, original data generation, first-cell artwork, exercises and citations.
- [x] `assets/` and `content/assets/` — save original generated splash image and generation provenance.
- [x] `README.md`, `ATTRIBUTIONS.md`, `CITATION.cff`, `LICENSE` — introduce the project, map launch destinations, distinguish used from linked sources, document licenses and credit contributors without claiming institutional endorsement.
- [x] `myst.yml`, `book/` — configure Jupyter Book 2, introduction, coverage matrix, official-access guide and bibliography.
- [x] `web/` — implement responsive static landing page and live interactive gallery for 2D/3D maps, scenes, globe, dashboard and more using synthetic data.
- [x] `scripts/`, requirements and `.github/workflows/` — reproducible local build, notebook validation, execution, artifact checks, and GitHub Pages deployment after a main push.
- [x] `tests/` — check meaningful numerical invariants, input rejection, coverage, splash presence, relative links and build outputs.

**Acceptance Criteria:**
- Given a clean environment, when dependencies install and the build runs, then the book, Lab and gallery produce a single static artifact suitable for repository-subpath hosting.
- Given each canonical notebook, when executed with a clean kernel, then all required synthetic cells complete without credentials and include assertions for analytical results.
- Given the book navigation, when a chapter is chosen, then the matching Lab notebook and source are identifiable.
- Given gallery controls, when a variable, time or rendering mode changes, then the figure updates and remains labeled synthetic with units and provenance.
- Given README links, when local routes are checked against the output artifact, then every configured experience resolves; externally blocked links are recorded honestly.
- Given a third-party data reference, when inspected in the attribution record, then it distinguishes conceptual citation, software dependency and actual data use.

## Implementation Notes

User authorization covers building and verifying all local artifacts. No intermediate approval is needed under the host instructions. Remote publication is not assumed; package the deployment workflow and report any remaining Pages activation step. Use Python/Pyodide for browser notebooks, Jupyter Book 2 for publishing, and small deterministic arrays to fit browser memory. Use conventional scientific plotting libraries for data visuals. Deployment URLs derive from the existing Git remote.

Original splash has already been generated using the built-in image-generation tool and saved at `assets/splash.png` and `content/assets/splash.png`; reuse these rather than generating again. Depicting an abstract globe and synthetic weather streamlines, it contains no official logos or copied photography. Primary official sources verified on 2026-11-15: https://destine.ecmwf.int/digital-twin-engine/ ; https://destine.ecmwf.int/climate-digital-twin/ ; https://destine.ecmwf.int/weather-induced-extremes-digital-twin/ ; https://github.com/destination-earth/DestinE ; https://polytope.readthedocs.io/en/stable/ ; https://destine-data-lake-docs.data.destination-earth.eu/en/latest/ ; https://data.destination-earth.eu/terms-and-conditions . The current Data Lake terms include restrictive redistribution/access clauses and attribution requirements: do not describe every DestinE dataset as freely redistributable or universally CC BY. The older generic data-policy page and newer terms differ, so point to the applicable dataset and service terms and do not redistribute authentic DT data. Generation 2 Climate DT metadata is available at https://www.ecmwf.int/en/forecasts/dataset/destination-earth-digital-twin-climate-change-adaptation-gen2 with DOI 10.21957/79c6af3105; only link, do not imply it was used. Source/code references must use small original paraphrases, not copied text. The installed Jupyter Book docs use version 2/MyST; JupyterLite quickstart currently shows jupyterlite-core 0.8.2 and jupyterlite-pyodide-kernel 0.8.3. Verify package availability. Use local virtualenvs; Python and uv available, node/npm not currently on PATH. Windows denies access to some temporary folders created by uv's runtime and may need an authorized elevated retry. Do not apply unrelated skills or add setup questioning; deliver the requested repository implementation.

## Spec Change Log

- Early implementation coverage audit: general scientific lessons need explicit named-component exercises to fulfill the original request. Include dedicated chapters for DTE orchestration/HPC roles, Polytope feature extraction, Earthkit and GRIB export, Data Lake HDA/STAC and Islet/Stack/Hook, ML temporal validation, and regional On-Demand Extremes. They must contain meaningful runnable local demonstrations and an explicit official-service transition, without suggesting that toy calculations implement the production service. Interactive Lab visualization must include working controls, not only static snapshots. These clarify existing acceptance and scope rather than introducing a separate goal.

## Review Triage Log

All three independent reviewers completed before triage. Each finding was assessed separately before grouping; all verified issues are small corrections within the existing implementation and route to `patch`.

| Finding | Verdict | Evidence and disposition |
|---|---|---|
| B1: globe longitude sign | medium | `globe()` adds the selected angle, so its center is the negative of the displayed view longitude. Correct the rotation sign. |
| B2: coordinate centers used as image edges | medium | Lessons 18 and 19 pass grid centers as `imshow` boundaries, shifting the displayed coordinates. Use coordinate-aware meshes. |
| B3: changing widget color limits | medium | Terrain, globe and dashboard widget branches normalize the selected frame independently. Set fixed per-variable limits so time comparisons are meaningful. |
| B4: visible back hemisphere | medium | Both globe scatter plots include all points with no opaque surface or culling while the explanation says a hemisphere is hidden. Cull back-facing points with the declared camera geometry. |
| B5: incomplete accessible gallery data | medium | All views expose the same three samples, omitting the dashboard series, comparison baseline and wind vectors. Extend the existing accessible table for those views. |
| B6: invalid interpolation grid | medium | `bilinear` has no minimum axis size or finite-value checks; singleton axes divide by zero and NaN values propagate. Validate the documented interpolation domain. |
| B7: NaN bucket capacity | medium | `capacity <= 0` does not reject NaN, allowing nonfinite water-balance results. Require finite positive capacity. |
| B8: empty spatial mean | medium | An empty longitude dimension passes the finite check and `mean` returns NaN. Reject empty spatial dimensions. |
| B9: repository-prefix links | medium | The artifact checker resolves `/lab/index.html` against the output root even under a configured repository prefix. Reject internal root-relative URLs outside that prefix. |
| B10: missing persistent browser-kernel check | medium | CI executes native Python but does not run Pyodide or widget controls. Preserve the demonstrated browser probe as a portable smoke check in CI. |
| E1: polar-only area weights | medium | Floating-point cosine residuals at ±90° normalize to plausible weights for a zero-area sample. Reject a numerically zero total. |
| E2: empty longitude mean | medium | Independently confirms B8: `field.mean(axis=-1)` accepts a zero-length longitude axis. Same patch group as B8. |
| E3: Boolean schema version | medium | Python equality permits `True == 1`, accepting an invalid version tag. Require exact integer type. |
| E4: Boolean numeric arrays | medium | Float coercion silently converts Boolean coordinates and field values to numbers. Reject Boolean entries before coercion, including mixed arrays. |
| E5: empty ensemble dimensions | medium | Zero members or days produce empty results that downstream lesson summaries cannot use. Require positive integer dimensions. |
| E6: nonfinite bucket capacity | medium | Independently confirms B7; no finite check precedes storage calculations. Same patch group as B7. |
| E7: empty/singleton interpolation axes | medium | Independently confirms B6; indexing or division can fail before a meaningful validation error. Same patch group as B6. |
| E8: nonfinite interpolation values | medium | Independently confirms B6; nonfinite coordinates/values can yield NaN results. Same patch group as B6. |
| E9: unknown selected notebook | medium | `--only` filters the file list without checking every requested stem, silently skipping a typo when another stem matches. Reject unknown names before starting kernels. |
| V1: gallery interaction verification | medium | Pre-verified: current tests check control markup, so removed event listeners pass CI. Add real control changes, numeric/units checks and canvas comparisons in the browser. |
| V2: browser package/runtime verification | medium | Pre-verified: native kernels skip the Pyodide installation branch. Same root cause as B10; run representative system, xarray and widget notebooks in fresh browser kernels. |

Patch groups retain all member outcomes: B6/E7/E8 (interpolation validation); B7/E6 (capacity validation); B8/E2 (empty spatial mean); B10/V2 (browser runtime verification). All remaining findings are independent direct corrections. Nothing is deferred.

Final coverage correction: the current official ECMWF ML component page explicitly lists land, waves, hydrology, sea ice and ocean. Added original lessons 29–32 for snow storage, wind-forced wave response, bounded ice fractions and two-layer heat exchange; hydrology is already in lesson 09 and temporal ML validation in lesson 27. These complete the named-component orientation without copying or claiming to run official models. Sources: https://destine.ecmwf.int/ml-earth-system-components/ and https://destine.ecmwf.int/ai-in-destination-earth/ (verified 2026-11-15). Shared book/Lab coverage is now 32 notebooks. A separate numerical review of the four added lessons accompanies clean-kernel execution.

| Follow-up finding | Verdict | Evidence and disposition |
|---|---|---|
| C1: wave exercise convergence horizon | medium | A fixed 40-step near-equilibrium assertion fails for the suggested 48-hour response time despite a stable update. Patched the check to compare the iterated finite-time solution with its analytical solution, preserving all suggested exercise values. |
| C2: navigation regeneration after component expansion | medium | The authoring helper still stopped navigation at lesson 28 and replaced authored coverage notes. Extended navigation to the complete manifest and preserved the component boundaries/credits. An isolated regeneration retained all 32 chapter links and the DTE/ML explanations. |

## Design Notes

One canonical notebook collection prevents book/Lab drift. Original synthetic data avoids redistributing uncertain-rights data and gives every learner an executable path. A coverage matrix separates implementation exercises from official infrastructure capabilities. Production examples must follow catalog-generated requests; do not invent working collection IDs or credentials. The gallery has standalone pages so README entries point to actual experiences rather than only source files.

## Verification

- Execute all notebooks natively and inspect outputs; validate at least representative notebooks in Pyodide/browser if available.
- Run unit tests for scientific invariants and schema errors.
- Build both products, verify required routes and asset references, and inspect the landing page and gallery in a browser.
- Report native execution separately from browser verification and remote publication.

## Final verification result

- 67 unit, input-validation, notebook-contract and build-contract tests passed with the final dependency lock.
- All 32 canonical notebooks completed in fresh native Python kernels; each retained a rendered PNG and its numerical assertions. Five also retain widget state. Added component figures and the corrected globe were visually inspected.
- The assembled Jupyter Book 2/JupyterLite/gallery build passed: 35 book pages, 45 required routes and 1,341 internal HTML/README references.
- Chromium verified all six galleries: variable/time/render changes, independently calculated numeric summaries and units, rotation, play/pause, view-specific accessible tables, mobile layouts and book navigation under the repository prefix.
- Fresh browser contexts executed 01-system, 05-labelled-arrays and 14-maps in Pyodide after clearing retained outputs. Verified actual xarray dimensions/results and an image change after the map widget selected precipitation. Browser verification is representative, not a claim that all 32 notebooks were individually run in Pyodide.
- Browser harness corrections: open collapsed tables before reading visible values; preserve the repository prefix in local directory redirects; wait for the target chapter heading; inspect the displayed widget image because Pyodide does not implement kernel user_expressions. Final evidence combines the successful gallery/book/01/05 checks with the targeted passing 14 run.
- Native Windows execution used ipykernel 6.31.0, a selector event loop, bounded per-cell waits and strict IOPub-output checking. A completed Windows run emitted a libzmq socket-teardown assertion; all 32 notebooks nevertheless completed with verified outputs. Some widget returns took about 33 seconds despite fast kernel calculations. The likely delayed socket-readiness notification is an inference, not a confirmed upstream regression. Linux CI and public deployment have not yet run.
- The suggested 6-, 18- and 48-hour wave response exercises passed after the review correction.
- All independent review findings were resolved; no product finding was deferred. Original artwork and source credits are present. No authentic DestinE data, model weights, external notebook code, agency images or credentials were included.
- Publication remains pending. README launch destinations are configured and local routes are verified; no push or public deployment has occurred.
