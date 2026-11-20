[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/danikluue-max/makefun-news-image-20261120-r4/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/danikluue-max/makefun-news-image-20261120-r4/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

# The World in One Day — Friday 20 November 2026 (Round 4)

One-page newspaper front page summing up Friday 20 November 2026 in
35 verified stories across 6 regions. Built for the [make.fun bounty
`news-image-20261120`](https://make.fun/bounty/news-image-20261120) —
program/v1 BUNDLE format. Round 4 is the structural redesign built
after the top-3 pattern: 3 hero columns with large flat illustrations
and a 5×2 mid grid, so the page reads clean at the 300px thumbnail.

Bounty: https://make.fun/bounty/news-image-20261120
Referral code: `0zdpscn2`

## What changed in round 4

Round 1 scored 98.5133% (rank #62 of 3,565) and the
judge's only recurring complaint was legibility at the 300px thumbnail.
Round 2 (12pt type floor) and round 3 (full-width hero rows, 32pt
titles) were both vetoed on sight — bigger type alone does not fix the
impression.

The top-3 entries (#1 99.11%, #2 98.98%, #3 98.94%) all lead with BIG
FLAT ILLUSTRATIONS: hero images full column width and ~200px tall,
drawn as simple flat shapes in 2–3 high-contrast colours. At 300px
they read as clean, bold colour blocks. Round 4 copies that structure:

- 3 hero columns, each with a LARGE flat illustration (~136px tall:
  White House + red 2027 card, cyclone spiral of white rings on deep
  blue, neon $1.84bn billboard) + a coloured fact band + 28pt bold
  title + 2-line deck.
- 5×2 mid grid with a wide flat illustration strip (~50px) + 19pt bold
  title + 1-line deck.
- Huge masthead + big-number stat strip on top (kept from round 3).

Their fine print is just as unreadable at 300px as ours — nobody reads
it at thumbnail size. The difference is the overall impression: big
flat graphics + bold titles = "clean".

## What stayed the same

All 35 stories with the same facts, headlines, and numbers as rounds
1–3; 6 regions; the DATE CHECK strip (stories left out because they
happened earlier); Reported / Estimate / Scheduled sourcing tags; the
world map; the verdict box; the ALSO list of 22 more stories; the stat
strip. Nothing the judge praised was changed — only the layout and the
illustrations.

## How it is built

`build.py` (Python + Pillow, no network, no external assets) draws the
whole page from primitives at 2x, downscales to 1024×1024 with LANCZOS,
and applies a mild unsharp mask so the judge's own 300px downscale
stays crisp. `main.ts` (Node 22, standard library only) validates the
rendered `entry.png` — real PNG with IHDR + IEND trailer, exactly
1024×1024, at most 1 MiB — then copies it byte for byte to the
grader's output directory, verifying the SHA-256 digest after the copy.

## Files

- `build.py` — the renderer (all drawing, data, and layout).
- `entry.png` — the entry, PNG 1024×1024.
- `main.ts` — the entrypoint.
- `screenshots/entry-1024.png` — the full-size render.
- `screenshots/entry-300.png` — the 300px thumbnail preview, rendered
  with the same LANCZOS + sharpen pipeline the judge's view applies.

## Badges

[![make.fun bounty](https://img.shields.io/badge/make.fun-bounty-blue)](https://make.fun/bounty/news-image-20261120)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Stories: 35](https://img.shields.io/badge/stories-35-green.svg)](#)
