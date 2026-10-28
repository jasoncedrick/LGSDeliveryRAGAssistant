# Website animation sources

These libraries are hosted locally. Visitors do not need a third-party CDN. Exact versions, download integrity and file hashes are recorded in `vendor/manifest.json`.

- **GSAP 3.15.0**, GreenSock/Webflow: https://github.com/greensock/GSAP. Its original copyright/license header is retained. Standard No Charge License: https://gsap.com/standard-license/. Used for short presentation entrance effects, not an animation-building product.
- **Lenis 1.3.27**, darkroom.engineering: https://github.com/darkroomengineering/lenis. MIT license retained in `vendor/lenis/LICENSE`. Used only for desktop informational-page scrolling; chat and touch retain native scroll.
- **React Bits**, David Haz: https://github.com/DavidHDev/react-bits. MIT plus Commons Clause terms retained in `vendor/react-bits/LICENSE.md`. The FadeContent reveal/cleanup pattern and StarBorder visual idea are adapted for this buildless application's `motion.js` and `motion.css`. This is an application integration, not a standalone component distribution. No React runtime or full component library is installed. The inspected commit is recorded in the manifest.

Adaptations omit blur, text splitting, continuous effects and scroll pinning. Device reduced-motion preference disables effects, and the user can turn decorative motion off. This preference alone is stored in the browser; conversation text is not stored by this feature.

Methodology boundary: these changes affect website presentation only (Chapter 3 section 3.2.6). They do not change prompts, queries, answers, source content, scoring, retrieval, evaluation artifacts or model settings. The separately documented response-language revision and its known quality limitations remain as recorded in `LANGUAGE_REVISION.md`.
