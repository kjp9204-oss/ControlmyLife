# Personal archive reconciliation — 2026-10-03

The approved black/white/red magazine remains the site design. Personal posts use exactly three top-level categories: anime, daily life and hobbies. AON, HandPhysio and Grand Library repositories are not modified by this release.

## Publication boundary

Only previously published personal material was added. Public Naver post IDs were cross-checked against the local completed-work inventory and recent public RSS; renamed articles were checked against their actual published prose. Local Word drafts, internal documents, clinical material and private audit files are not publication inputs.

The original 83 archive entries and historical static article URLs remain. Ten existing manually created articles were compared with their public Naver equivalents and excluded from duplicate listing. Multiple local draft/revision filenames never create multiple archive records for the same public ID.

## Images and prose

This reconciliation adds 288 previously published posts to the original 83: 371 archive entries in total, grouped into 198 anime, 13 daily-life and 160 hobby entries. The archive has 6,254 body-image references. Twenty-nine unpublished Word drafts remain outside this release and require separate review.

There are 126 unavailable external-image references across 72 added posts, each represented by an original-page link, and 23 original-page video links. These are not counted as locally recovered photographs or playable local videos.

Published prose and image order are preserved. Added image files use high-quality web derivatives where useful, with original files and conversion recovery records retained privately off-site. Existing published photos are unchanged. Animated GIFs are converted only when frame count, frame delays and looping are retained; otherwise the original GIF stays.

Unavailable or blocked external images retain a visible link to the Naver original; no replacement illustration is invented. Embedded videos retain original-page playback links rather than being represented as locally playable video files.

This is an archive migration, not a fresh fact-check, medical review or comprehensive republication-rights audit of historical articles.

## Rebuild safety

The source app and private QA material remain in the local Control Mylife project. The release checkout receives only the built public entry/assets/content, published static article pages, public metadata, sitemap and these notes. Local caches and runtime bytecode are not website files.

Before committing, verify original article hashes, existing image bytes, public-source prose, all archive routes, image decoding, category/search/pagination, mobile reflow and error recovery. A successful build alone is not the deployment check.

Local release gates completed on 2026-10-04: 428 functional checks, including all 371 bodies and 6,254 photo references; 383 resilience checks, including every reader at 320px; and four static-serving tests. Normal browser navigation recorded no console/script errors or failed requests. Wide article tables scroll inside the reader on small screens.
