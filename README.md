# sasakuruppuarachchi.github.io

Personal portfolio of Sasanka Kuruppu Arachchige: research, projects, publications and media.
Plain Jekyll on GitHub Pages, with a small hand-written design system. There is no theme gem, jQuery
or icon font.

## Structure

| Path | What it is |
|---|---|
| `index.html` | Home: intro, "Currently working on", recent work, selected publications, media, contact |
| `posts.html` | All work with topic filter chips, newest/oldest sort and a year timeline in the sidebar (`?topic=robotics` deep-links a filter) |
| `publications.html` | Rendered from `_data/publications.yml` (+ anything new on ORCID, from `_data/orcid.json`) |
| `contact.html`, `photography.html`, `404.html` | Other pages |
| `_posts/` | One file per project/event. URLs follow Jekyll's default `date` permalink and must not change |
| `_layouts/` | `default` (sidebar + top bar + footer), `post`, `redirect` |
| `_includes/` | `sidebar`, `nav`, `footer`, `card`, `pub`, `filter-chips`, `icon` (inline SVG icons), `lightbox` |
| `_data/` | `publications.yml` (curated), `categories.yml` (chip labels/order), `orcid.json` and `videos.json` (auto-updated) |
| `assets/css/site.css` | The whole stylesheet: tokens, light/dark, components |
| `assets/js/site.js` | All interactions (vanilla JS) |
| `assets/thumbs/` | Generated card thumbnails (see below) |

## Writing a post

```bash
python3 scripts/new_post.py --title "My Project" --date 2026-11-07 \
  --categories "Projects: Robotic, RAICAM" --cover "/assets/media/2026/11/cover.gif" \
  --abstract "One or two sentences." --status Ongoing
python3 scripts/make_thumbs.py      # generate the card thumbnails for the new cover
```

Front matter fields used by the site:

- `title`, `date`, `categories`, `tags`
- `abstract`: the card text. Keep it to 1–2 sentences.
- `cover`: the original image or GIF. Always use an absolute path (`/assets/...`).
- `thumb` / `thumb_anim`: written by `make_thumbs.py`. The static poster shows first; the animated
  preview plays on hover (desktop) or when the card is centred (phones).
- `status`: `Ongoing` adds the live badge and lists the post under "Currently working on".
- `visibility`: only `Published` posts are listed.
- `redirect_to`: the card links straight to an external project page.

Post bodies can be HTML or Markdown. Every image inside a post opens in the lightbox; galleries use
`.masonry-gallery`, `.gallery-grid` or `.two-up`, and videos use `.video-container`.

## Publications

Edit `_data/publications.yml`. It has three groups, `published`, `review` and `prep`. Each entry
supports `doi`, `arxiv`, `url`, `project`, `code`, `video`, `award`, and `post` (the slug of a related
post). BibTeX is generated automatically. A daily GitHub Action
(`.github/workflows/update-publications.yml`) refreshes `_data/orcid.json` and `_data/videos.json`. Any
ORCID work that isn't in the curated list appears under "Also indexed on ORCID" until you add it.

## Local preview

The easiest way is Docker, which uses the same gem set as GitHub Pages:

```bash
docker run --rm -it -p 4000:4000 -v "$PWD":/srv -w /srv ruby:3.3 \
  bash -c "bundle install && bundle exec jekyll serve --host 0.0.0.0"
```

Or with a local Ruby: `bundle install && bundle exec jekyll serve`.

## Scripts

| Script | Purpose |
|---|---|
| `make_thumbs.py` | Builds `assets/thumbs/*.webp` posters and animated previews, and records them in front matter |
| `new_post.py` | Scaffolds a post |
| `fetch_orcid.py` / `fetch_scholar.py` | Publication snapshot into `_data/orcid.json` |
| `fetch_youtube.py` | Latest channel videos into `_data/videos.json` |
| `add_covers.py`, `add_abstracts.py`, `add_post_flags.py`, `import_wordpress.py` | One-off migration helpers from the WordPress era |
