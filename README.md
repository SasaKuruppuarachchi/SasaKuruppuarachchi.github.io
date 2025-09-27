## Portfolio site (Jekyll + Strata theme)

This is the source for my personal portfolio website, built on Jekyll using a customized Strata theme.

Highlights:
- Posts listing with cover images, short abstracts, category filter, and newest/oldest sort.
- Homepage “Recent Work” shows the latest posts with the same controls, compact and inline.
- Single post layout with convenient navigation (Back Home, All Posts).
- Polished UI details: thumbnail hover overlays, unified card typography, and dark‑mode heading fixes.
- Helper scripts to scaffold posts, backfill covers/abstracts, import WordPress, and fetch publications.


## Local development

Prerequisites:
- Ruby and Bundler
- Jekyll

Quick start:
1) Install dependencies (first time):
	 - gem install bundler jekyll
	 - bundle install
2) Run the dev server:
	 - bundle exec jekyll serve
3) Open http://127.0.0.1:4000

Configuration lives in `_config.yml`. Site layouts are under `_layouts/`, includes in `_includes/`, styles in `assets/css/` (theme) and `assets/css/custom.css` (overrides).


## Authoring content

Posts live in `_posts/` with filenames like `YYYY-MM-DD-slug.html` and front matter:

---
layout: post
title: "My Post Title"
date: 2025-09-27 12:00:00
categories: ["Category A", "Category B"]
tags: ["tag1", "tag2"]
cover: "/assets/media/2025/09/cover.jpg"   # optional
abstract: "One or two sentences about the post."   # optional
---

Body content can be HTML or Markdown. If you don’t set `cover`, the site (and helper scripts) can infer it from the first `<img>` in the body. You can flag a specific image as the cover by adding `data-cover` or `data-thumb` on that `<img>` tag.

Abstracts: If you don’t set `abstract`, a helper can generate one from the first paragraph.


## UI behavior you should know

- Posts list (`posts.html`) and homepage (“Recent Work”) both support:
	- Category filter: “All” plus any categories used in posts.
	- Sort by: Newest (default) or Oldest.
- Post cards show a cover image with a subtle hover overlay and a truncated abstract.
- Dark mode: h1/h2 are explicitly set to white for readability.
- Single post pages include quick nav buttons at the bottom: “← Back Home” and “All Posts”.


## Scripts

All scripts live under `scripts/`. Use `python3` and a recent Python 3.x.

1) Create a new post scaffold
- File: `scripts/new_post.py`
- What it does: creates `_posts/YYYY-MM-DD-slug.html` with proper front matter and a stub body.
- Usage:
	- python3 scripts/new_post.py --title "My Post" --date 2025-09-27 --categories "Robotics, Research" --tags "tag1,tag2" --cover "/assets/media/2025/09/cover.jpg" --abstract "One-liner" --force
	- Example used to create an actual post in this repo:
		 ```python3 scripts/new_post.py --title "Korea Robot Aircraft Contest 2023" --date 2023-09-02 --categories "Robotics Projects" --cover "assets/media/2023/09/IMG_20230722_080348.jpg" --abstract "One-liner" --force```

2) Auto-add cover images to posts
- File: `scripts/add_covers.py`
- What it does: adds `cover: "..."` to front matter by picking the first `<img>` with `data-cover`/`data-thumb`, or the first image in the body.
- Usage:
	- Dry-run: python3 scripts/add_covers.py
	- Write changes: python3 scripts/add_covers.py --write
	- Verbose: add `--verbose`

3) Auto-generate abstracts for posts
- File: `scripts/add_abstracts.py`
- What it does: generates a short abstract (1–2 sentences) from the first paragraph and inserts `abstract:` into front matter if missing.
- Usage:
	- Dry-run: python3 scripts/add_abstracts.py
	- Write changes: python3 scripts/add_abstracts.py --write
	- Verbose: add `--verbose`

4) Import WordPress export (WXR) into Jekyll posts
- File: `scripts/import_wordpress.py`
- What it does: converts a WordPress XML export into `_posts/*.html`, rewrites media URLs from `/wp-content/uploads/...` to `/assets/media/...`, and preserves HTML content.
- Usage:
	- python3 scripts/import_wordpress.py lagacy/sasankakuruppuaarachchige.WordPress.2025-09-25.xml
	- Note: Place your WXR file under `lagacy/` (as in this repo) or pass an absolute path.

5) Fetch publications from ORCID
- File: `scripts/fetch_orcid.py`
- What it does: pulls works from the ORCID public API and writes `data/publications.json` with a compact schema.
- Usage:
	- python3 scripts/fetch_orcid.py
	- Environment variables:
		- ORCID_ID to override the default ORCID.
		- ORCID_FETCH_DETAILS=1 to fetch per‑work details for authors (slower).

6) Fetch publications from Google Scholar (best-effort)
- File: `scripts/fetch_scholar.py`
- What it does: scrapes the first page of Google Scholar and writes `data/publications.json`. If a CAPTCHA is detected, it skips updating to avoid clobbering.
- Usage:
	- python3 scripts/fetch_scholar.py


## Media and paths

- Site media is under `assets/media/YYYY/MM/...`.
- The WordPress import and cover detection expect this layout. If you are migrating, mirror your uploads there.


## Repository structure (short)

- `_layouts/` and `_includes/`: Liquid templates for pages and posts.
- `_posts/`: Your posts (HTML/Markdown) with YAML front matter.
- `assets/css/`: Theme CSS and `custom.css` for overrides and new styles.
- `assets/js/`: Client-side JS for filtering/sorting and dynamic sections.
- `data/publications.json`: Publications list rendered on the site.
- `scripts/`: Python utilities listed above.


## Credits and license

- Theme: Strata by HTML5 UP, ported to Jekyll. See `LICENSE.txt` for theme licensing.
- This repository’s custom code and documentation are provided under the same license as the theme unless stated otherwise.

For general Jekyll docs, visit https://jekyllrb.com/. For front matter basics, see https://jekyllrb.com/docs/front-matter/.
