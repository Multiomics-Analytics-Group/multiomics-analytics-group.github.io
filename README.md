# MoNA website

Source of the Multi-omics Network Analytics (MoNA) group website: <https://multiomics-analytics-group.github.io>

The site is built with [Jekyll](https://jekyllrb.com/) and [GitHub Pages](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll) on top of the [Hyde](https://github.com/poole/hyde) theme. The **Research**, **Tools**, **Education** and **People** pages, and the highlights on the **Home** page, are generated automatically from a few simple files. To update them you edit a list, open a pull request and a GitHub Actions workflow does the rest.

- [Updating the website](#updating-the-website)
  - [Which file do I edit?](#which-file-do-i-edit)
  - [Step by step](#step-by-step)
  - [Publications (Research page)](#publications-research-page)
  - [Tools and courses (Tools and Education pages)](#tools-and-courses-tools-and-education-pages)
  - [People](#people)
  - [Home page](#home-page)
  - [Fixing what was extracted (overrides)](#fixing-what-was-extracted-overrides)
- [What happens behind the scenes](#what-happens-behind-the-scenes)
  - [On a branch / pull request](#on-a-branch--pull-request)
  - [On master](#on-master)
  - [Monthly refresh and manual runs](#monthly-refresh-and-manual-runs)
  - [Troubleshooting](#troubleshooting)
- [Other content](#other-content)
- [Previewing locally](#previewing-locally)
- [Repository layout](#repository-layout)
- [Styling](#styling)
- [Credits and license](#credits-and-license)


## Updating the website

### Which file do I edit?

| I want to… | Edit this file | What you provide |
|---|---|---|
| Add a **publication** (Research page) | [`_content/publications.yml`](_content/publications.yml) | the paper's URL or DOI link |
| Add a **tool** (Tools page) | [`_content/tools.yml`](_content/tools.yml) | the GitHub repository URL |
| Add a **course** (Education page) | [`_content/courses.yml`](_content/courses.yml) | the GitHub repository URL |
| Add, update or move a **person** to alumni (People page) | [`_content/people.yml`](_content/people.yml) + a photo in [`public/assets/people/`](public/assets/people/) | name, surname, position, photo |
| Show an item under a **research theme** on the Home page | the item's entry in `_content/*.yml` | `themes: [...]` |

Everything else (titles, abstracts, figures, README summaries, cropped photos, ordering newest to oldest) is produced by the workflow. **Never edit `_data/auto_*.json` or `public/auto/` by hand**: they are overwritten on every run.

### Step by step

You can do this entirely in the GitHub web interface (easiest) or with git on your computer.

**In the browser**

1. Open the file you need (see the table above) on GitHub and click the pencil icon (*Edit this file*).
   To add a photo, open [`public/assets/people/`](public/assets/people/) and use *Add file → Upload files*.
2. Make your change. Copy the format of an existing entry; indentation matters in YAML (use spaces, not tabs).
3. Click *Commit changes…*, choose **Create a new branch for this commit and start a pull request**, give the branch a short name (e.g. `add-abaco-paper`) and click *Propose changes*.
4. On the pull request page, write one line describing the change and click *Create pull request*.
5. **Ask for a review.** A repository admin is added as reviewer automatically (see [`CODEOWNERS`](CODEOWNERS)). If nobody is listed under *Reviewers*, add one there and mention them in a comment so they get notified.
6. Wait 1–3 minutes for the check **Update publications, tools, courses and people** to finish:
   - ✅ green: the bot has added a commit called *Update auto-generated publications, tools and courses* with the generated content. Open the *Files changed* tab to check titles, summaries and images.
   - ❌ red: open *Details* → *Summary*. It lists every entry that needs attention and how to fix it (see [Troubleshooting](#troubleshooting)). Fix the entry by editing the same file on your branch; the check runs again.
7. An admin reviews and merges the pull request. The website updates a few minutes later.

**With git**

```bash
git clone git@github.com:Multiomics-Analytics-Group/multiomics-analytics-group.github.io.git
cd multiomics-analytics-group.github.io
git switch master && git pull
git switch -c add-abaco-paper            # one branch per change

# edit _content/publications.yml (or tools/courses/people)
git add _content/publications.yml
git commit -m "Add ABaCo paper"
git push -u origin add-abaco-paper
```

Then open the pull request on GitHub and continue from step 4 above. The bot pushes a commit to your branch, so run `git pull` before pushing further changes.

> `master` is protected: changes can only reach it through a reviewed pull request. Pushing directly to `master` is rejected.

### Publications (Research page)

Add the link to [`_content/publications.yml`](_content/publications.yml):

```yaml
- url: https://www.biorxiv.org/content/10.64898/2026.10.27.762128v1
  short: IBD graph neural networks     # optional: short label used on the Home page
  themes: [graph-ml, microbes]         # optional: Home page research themes
```

Supported links: `https://doi.org/<DOI>` (always works), bioRxiv/medRxiv, nature.com, academic.oup.com, ScienceDirect/Cell, PubMed/PMC and any journal page that exposes its DOI. The workflow fetches the title, authors, date, journal, abstract and a figure (Figure 1 or the graphical abstract when available) and lists publications newest first.

### Tools and courses (Tools and Education pages)

Add the GitHub repository to [`_content/tools.yml`](_content/tools.yml) or [`_content/courses.yml`](_content/courses.yml):

```yaml
- url: https://github.com/Multiomics-Analytics-Group/InstaNexus
  themes: [generative]
```

From the README the workflow takes the title, the opening paragraph(s), the bullets under a *Features* / *Objectives* heading, a *Keywords* section and the first suitable image (badges and rows of institutional logos are skipped). Items are ordered by the repository's creation date, newest first.

Tip: the result is only as good as the README. A clear first paragraph, a *Features* or *Objectives* list and a figure near the top give the best page.

### People

Edit [`_content/people.yml`](_content/people.yml). It has two sections, `active` and `alumni`; people appear in the order of the file, grouped by `team`.

```yaml
active:
  - name: Jane
    surname: Doe
    position: PhD Student                  # or a list for several roles
    team: Multi-omics Network Analytics (MoNA)
    email: jado@dtu.dk                     # optional
    photo: public/assets/people/jane_doe.jpg
    github: janedoe                        # optional: website, github, linkedin, orcid, scholar, bluesky, x

alumni:
  - name: John
    surname: Roe
    position: Postdoc
    years: 2021-2024                       # optional
    now: Data Scientist at Company X       # optional
    photo: public/assets/people/john_roe.jpg
```

- Upload the original photo to `public/assets/people/` (any size or format, ideally a head-and-shoulders portrait). The workflow crops it to a square and resizes it so all cards look the same. Without a photo the card shows the person's initials.
- If the crop cuts the face, add `photo_focus` (0 = top, 0.5 = centre; default 0.25) and/or `photo_zoom` (e.g. `1.3` for a photo taken from far away).
- When someone leaves: move their entry from `active` to `alumni` and optionally add `years` and `now`.

### Home page

- **Latest publications, Tools and Courses** on the Home page update automatically from the files above.
- **Research themes** are written in [`_data/home_themes.yml`](_data/home_themes.yml). A publication, tool or course is linked under a theme when its entry has `themes:` with the theme id: `graph-ml`, `knowledge-graphs`, `generative`, `microbes`, `data`, `training`.
- The vision and *Where we are heading* texts are edited directly in [`index.html`](index.html) (ask an admin before changing them).

### Fixing what was extracted (overrides)

Any field can be set by hand in the entry and always wins over the fetched value:

```yaml
- url: https://github.com/Multiomics-Analytics-Group/course_graph_machine_learning
  title: Graph Machine Learning
  summary: >-
    A short description in **Markdown** that replaces the README text.
  highlights:
    - First objective
    - Second objective
  image: public/assets/my_figure.png       # or an image URL
  date: 2025-01-10                         # changes the ordering
```

| Field | Publications | Tools / courses |
|---|---|---|
| `title`, `date`, `image`, `hidden: true` | ✓ | ✓ |
| `doi`, `authors`, `venue`, `abstract`, `image_caption`, `short` | ✓ | |
| `description` (subtitle), `summary`, `highlights`, `keywords`, `homepage`, `note` | | ✓ |
| `embed` (HTML page shown in a frame), `embed_title` | | tools |
| `themes` | ✓ | ✓ |

`hidden: true` keeps an entry in the file but removes it from the website.


## What happens behind the scenes

All automation lives in the workflow [`.github/workflows/update-content.yml`](.github/workflows/update-content.yml), which runs [`scripts/update_site_content.py`](scripts/update_site_content.py).

```
edit _content/*.yml ──► pull request ──► workflow generates content ──► bot commits to the PR branch
                                                                                  │
          website updated ◄── GitHub Pages rebuilds ◄── admin reviews & merges ◄──┘
```

### On a branch / pull request

Triggered when a pull request changes `_content/`, `public/assets/people/`, the script or the workflow.

1. Fetches metadata, abstracts, README text and images for **new or changed** entries only (unchanged entries are reused from `_data/auto_*.json`).
2. Writes `_data/auto_*.json` and the images in `public/auto/`, and **commits them to the pull request branch**, so the generated content is reviewed and merged together with your change.
3. Writes a summary of problem entries on the run page and marks the check red if an entry could not be generated. Entries that worked are still committed.

Pull requests from forks get the check and a downloadable `generated-content` artifact, but no bot commit.

Pushing to a branch without opening a pull request does nothing.

### On master

- Merging a pull request makes **GitHub Pages rebuild the site** (usually within a few minutes; see the repository's *Actions → pages-build-deployment*).
- The workflow also runs after the merge as a safety net. Normally nothing has changed and it stops. If something did change (e.g. a figure that failed before is now available), it opens a pull request **"Update auto-generated site content"** from the branch `bot/update-site-content` for an admin to merge.

### Monthly refresh and manual runs

- On the 1st of every month the workflow re-fetches everything (new preprint versions, updated READMEs) and, if anything changed, opens the same **"Update auto-generated site content"** pull request.
- Admins can run it any time from *Actions → Update publications, tools, courses and people → Run workflow* (tick *refresh* to re-fetch everything).

### Troubleshooting

| Problem | Fix |
|---|---|
| *could not find a DOI for this URL* | Use the `https://doi.org/<DOI>` link instead, or add `doi:` to the entry. |
| *no figure could be downloaded* | Some publishers block automatic downloads. Add `image:` with a figure URL or a file uploaded to `public/assets/`. |
| *no abstract found* | Very recent papers may not be indexed yet. Add `abstract:` or wait for the monthly refresh. |
| Wrong or ugly image for a tool/course | Add `image:` to the entry. |
| Poor summary for a tool/course | Improve the README, or add `summary:` (and `highlights:`) to the entry. |
| A photo is badly cropped | Add `photo_focus` / `photo_zoom` to the person. |
| `git push` rejected on your branch | The bot added a commit: run `git pull`, then push again. |
| YAML error | Check indentation (spaces only) and that every entry starts with `- `. |


## Other content

These pages are still edited by hand (open a pull request in the same way):

| Content | File |
|---|---|
| Contact page | [`6contact.md`](6contact.md) |
| Hand-written tools and courses kept below the generated ones | [`3tools.md`](3tools.md), [`4education.md`](4education.md) |
| Home page vision text | [`index.html`](index.html) |
| Sidebar links | [`_includes/sidebar.html`](_includes/sidebar.html) (`sidebar-nav-item`) |

Pages appear in the top menu in file-name order (hence the numeric prefixes). A new page needs this front matter at the top:

```yaml
---
layout: page
title: Contact          # text shown in the menu
permalink: /contact/    # URL of the page
---
```

Files without front matter (such as this README) are not published. Put static files (images, PDFs) in `public/assets/`.


## Previewing locally

Optional, for larger changes:

```bash
# generate content (needs internet access)
pip install -r scripts/requirements.txt
python scripts/update_site_content.py              # only new/changed entries
python scripts/update_site_content.py --kind people
python scripts/update_site_content.py --refresh    # re-fetch everything

# build and serve the site (https://jekyllrb.com/docs/installation/)
jekyll serve --watch
```

Do not commit the generated files from a local run unless an admin asks you to; the workflow produces them on the pull request.


## Repository layout

```
/
├── index.html                  Home page (vision text + automatic highlights)
├── 1research.md                Research page (publications)
├── 3tools.md                   Tools page
├── 4education.md               Education page
├── 5people.md                  People page
├── 6contact.md                 Contact page
├── CODEOWNERS                  admins requested automatically as reviewers
├── _content/                   ✏️  what you edit
│   ├── publications.yml
│   ├── tools.yml
│   ├── courses.yml
│   └── people.yml
├── _data/
│   ├── home_themes.yml         ✏️  Home page research themes
│   └── auto_*.json             🤖 generated, do not edit
├── _includes/                  page templates (auto_*.html render the generated data)
├── _layouts/                   site layouts
├── public/
│   ├── assets/                 static files; people/ holds original photos
│   ├── auto/                   🤖 generated figures and photos, do not edit
│   └── css/                    styles (auto-content.css, home.css, Hyde theme)
├── scripts/
│   └── update_site_content.py  the generator run by the workflow
└── .github/workflows/
    └── update-content.yml      the workflow
```


## Styling

:warning: Changes to `_includes/`, `_layouts/` and `public/css/` affect every page and need HTML/CSS knowledge. Please discuss them with an admin first.

- Generated content: `public/css/auto-content.css`; Home page: `public/css/home.css`.
- Theme: [Hyde](https://github.com/poole/hyde) (`public/css/hyde.css`, `poole.css`).


## Credits and license

Based on [Hyde](https://github.com/poole/hyde) by [Mark Otto](https://github.com/mdo). Open sourced under the [MIT license](LICENSE.md).
