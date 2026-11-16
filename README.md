# MoNA website

This website was created using [jekyll](https://jekyllrb.com/) and [GitHub Pages](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll). 

Jekyll is a static site generator that takes care of updating a site template with contents of our chosing, which we can provide via markdown files. 

The site template is [Hyde (see repo for more details)](https://github.com/poole/hyde) with some of our own modifications.

Included are instructions for how to update the team website with a focus on the content rather than styling. 

- [MoNA website](#mona-website)
  - [Directory organization](#directory-organization)
  - [MUST READ - how jekyll works](#must-read---how-jekyll-works)
    - [Home page (default) vs. all other pages](#home-page-default-vs-all-other-pages)
  - [Updating website content](#updating-website-content)
    - [(OPTIONAL) Previewing changes locally](#optional-previewing-changes-locally)
    - [Updating an existing page](#updating-an-existing-page)
    - [Adding a page (example)](#adding-a-page-example)
    - [Updating side nav links](#updating-side-nav-links)
  - [Publications, tools and courses (automated)](#publications-tools-and-courses-automated)
  - [Updating the styling ](#updating-the-styling)
  - [Original Author](#original-author)
  - [License](#license)


## Directory organization of Repo

(only highlighting folders and files relevant to updating site)

```bash
/
├── index.md
├── 1research.md
├── 2ds_platform.md
├── 3people.md
├── 4tools.md
├── 5education.md
├── 6contact.md
├── README.md
├── _config.yml
├── _includes/
│   ├── head.html
│   └── sidebar.html
├── _layouts/
│   ├── default.html
│   └── page.html
├── _site/
└── public/
    ├── assets/
    └── css/

```


## MUST READ - how jekyll works

1.  How jekyll knows to work its magic on a markdown or html file is based on the file's [YAML front matter block](https://jekyllrb.com/docs/front-matter/). 
  
  e.g., 
  ```
  ---
  layout: page
  title: About
  permalink: /about/
  ---
  ```
- **no front matter = not included in the website** (e.g., jekyll knows not to include this README.md you are reading because there is no front matter)

2.  Main takeaway: To update the **contents of the website** you will only need to add/remove/update the markdown files with front matter in the main directory. (e.g., [3people.md](3people.md)) More instructions in [Updating website content](#updating-website-content).

- **Do not alter the files in `_includes`, `_layouts` for now.**


#### Home page (default) vs. all other pages

- How jekyll knows to work its magic on a markdown or html file is based on the file's [YAML front matter block](https://jekyllrb.com/docs/front-matter/). 
  
- Currently, there are 2 page layouts (templates) used in our site:
  - `default` via */_layouts/default.html*
  - `page` via */_layouts/page.html`*
  
- The way that the styling is merged with the markdown files is via `layout` in the front matter: 
  e.g.,
  ```
  ---
  layout: page
  title: About
  permalink: /about/
  ---
  ```
- `layout: page` is to be used for almost all of the pages you want included in the site
- `layout: default` is only used for the home page [index.md](index.md) because it has some additional formatting + appears as the first option in the top menu bar
  >From the Hyde repo: "**Why require a specific layout?** Jekyll will return *all* pages, including the `atom.xml`, and with an alphabetical sort order. To ensure the first link is *Home*, we exclude the `index.md` page from this list by specifying the `default` layout."


## Updating website content

- To update the contents of the website you will only need to add/remove/update markdown files in the main directory. 
- To incorporate images or any other files into the site please put them in `/public/assets/`
  
#### (OPTIONAL) Previewing changes locally
If you want to test/preview the site locally as you make changes 

1. [install jekyll](https://jekyllrb.com/docs/installation/)
2. in your terminal cd into the site's repo 
3. then run `jekyll serve --watch`
4. open the url in `Server address: ...`
5. To preview your changes don't forget to save your file and refresh the browser.

#### Updating an existing page

1. Clone this repository
2. Create a branch from the 'master' branch of THIS repository (not the poole/hyde one)
3. In the main directory, open the markdown file you want to update e.g. [3people.md](3people.md)
4. make whatever changes to the content you want 
5. save the file 
6. push the changes to your branch
7. Make a pull request for your branch into the **MoNA's `Master` branch** (:warning: NOT poole/hyde) then jekyll will take care of the rest
  
(it's that easy :smiley:)


#### Adding a page (example)
Let's say you want to add a 'Contact' page and it should appear as the last option on the top menu bar

1. Steps 1-3 in [Updating an existing page](#updating-an-existing-page)
2. Create a markdown file in the root directory. Since pages are sorted alphabetically, if you want the Contact page to be last in the menubar of the website, prefix the markdown filename with a '9' or 'z' for example
3.  In the markdown file, the front matter should look like this:
  
  ```
  ---
  layout: page
  title: Contact
  permalink: /contact/
  ---
  ```
  - the layout should be 'page', to tell jekyll to use the page.html layout
  - the title is what will be used in the top menu bar
  - assigning a permalink will overwrite the default of using the ugly filename (e.g., `... .github.io/contact/` instead of `... .github.io/9contact/`)

4. Underneath the front matter include whatever content you would like. You can add formatting to the file using markdown or html syntax.
5. Steps 5-7 in [Updating an existing page](#updating-an-existing-page)


#### Updating side nav links
- similar steps to those in [Updating an existing page](#updating-an-existing-page)
- However, the file that needs to be updated is `/_includes/sidebar.html`
- Look for the `sidebar-nav-item` tags


## Publications, tools and courses (automated)

The **Research → Publications**, **Tools** and **Education → Courses** lists are generated automatically from three link lists. You only add a URL; a GitHub Actions workflow does the rest.

| Page | File to edit | What is extracted |
|------|--------------|-------------------|
| Research (Publications) | [`_content/publications.yml`](_content/publications.yml) | title, authors, date, journal/preprint server, abstract and a figure (Figure 1 for bioRxiv/medRxiv) |
| Tools | [`_content/tools.yml`](_content/tools.yml) | README title, repository description, opening README paragraph(s), "Features" bullets, first suitable README image, topics |
| Education (Courses) | [`_content/courses.yml`](_content/courses.yml) | README title, opening paragraph(s), "Objectives" bullets, "Keywords", first suitable README image |

Entries are shown **newest to oldest** (publication date, or repository creation date for tools and courses).

#### Adding an item

1. Create a branch and add an entry to the right file, e.g.
   ```yaml
   - url: https://www.biorxiv.org/content/10.64898/2026.10.27.762128v1
   ```
2. Open a pull request. The workflow **Update publications, tools and courses** checks that every link can be resolved, generates `_data/auto_*.json` and the images in `public/auto/`, and commits them to your PR branch (pull before pushing more changes).
3. Review the generated commit and merge. GitHub Pages rebuilds the site.

#### Overriding what is extracted

Any field can be set by hand in the YAML entry and takes priority over the fetched value, for example when no figure can be downloaded or a README image is not the one you want:

```yaml
- url: https://github.com/Multiomics-Analytics-Group/course_multi-omics_analysis
  image: https://raw.githubusercontent.com/Multiomics-Analytics-Group/course_multi-omics_analysis/main/figures/overview.png
  date: 2026-05-01
  highlights:
    - Process MS-based proteomics and metabolomics data in Python
    - Integrate multi-omics data with networks
```

Common overrides: `title`, `date`, `image` (URL or repo path like `public/assets/fig.png`), `abstract` (publications), `summary` / `highlights` / `description` / `keywords` (tools and courses), `hidden: true` (hide without deleting).

#### Running it locally

```bash
pip install -r scripts/requirements.txt
python scripts/update_site_content.py            # only new/changed entries
python scripts/update_site_content.py --refresh  # re-fetch everything
```

The workflow can also be run by hand from the **Actions** tab (tick *refresh* to re-fetch everything), and it refreshes everything automatically on the 1st of each month. Because `master` only accepts changes through pull requests, these runs open a PR (`Update auto-generated site content`) that you merge to publish.

:warning: Do not edit `_data/auto_*.json` or `public/auto/` by hand; they are overwritten by the workflow. Hand-written tools and courses already on the pages are kept below the generated ones.


##  Updating the styling 
**:warning: Dangerous territory**

- Recall that the site template is [Hyde (see repo for more details)](https://github.com/poole/hyde) with some of our own modifications.
- Updates to formating is done in the 3 directories: `/_includes/` `/_layouts/` and `/public/`
- Requires HTML and CSS 


## Original Author
[Please see hyde repo for more details](https://github.com/poole/hyde)
**Mark Otto**
- <https://github.com/mdo>
- <https://twitter.com/mdo>

## License
Open sourced under the [MIT license](LICENSE.md).

<3
