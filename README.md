# MoNA website

This website was created using [jekyll](https://jekyllrb.com/) and [GitHub Pages](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll). 

Jekyll is a static site generator that takes care of updating a site template with contents of our chosing, which we can provide via markdown files. 

The site template is [Hyde (see repo for more details)](https://github.com/poole/hyde) with some of our own modifications.

Included are instructions for how to update the team website with a focus on the content rather than formating. 

- [MoNA website](#mona-website)
  - [Contents](#contents)
    - [Directory organization](#directory-organization)
    - [Home page (default) vs. all other pages](#home-page-default-vs-all-other-pages)
      - [Adding a page (example)](#adding-a-page-example)
      - [Updating an existing page](#updating-an-existing-page)
    - [Added Top menu](#added-top-menu)
  - [Original Author](#original-author)
  - [License](#license)

## Contents

### Directory organization

- Main takeaway: To update the contents of the website you will only need to add/remove/update markdown files in the main directory. 
- To incorporate images or any other files into the site please put them in `/public/assets/`
- Extra: To update any other formating the only 2 directories you need to care about are `/_layouts/` and `_public`

### Home page (default) vs. all other pages

- How jekyll knows to work its magic on a markdown or html file is based on the file's [YAML front matter block](https://jekyllrb.com/docs/front-matter/). 
  
- no front matter = not included in the website (e.g., this readme)
  
- Currently, there are 2 page layouts used in our site:
  - `/_layouts/default.html`
  - `/_layouts/page.html`

- The way that they are merged with the markdown files is via the front matter: 
```
---
layout: page
title: About
permalink: /about/
---
```
- `layout: default` should only be used for the home page because it has some additional formatting + appears as the first option in the top menu bar
- `layout: page` is used for all other pages you want included in the site. More instructions for adding a new page below. 

#### Adding a page (example)

- Let's say you want to add a 'Contact' page and it should appear as the last option on the top menu bar

#### Updating an existing page

- In the main directory, open the markdown file
- make the changes you want 
- save it and make a pull request

### Added Top menu

Create a list of nav links in the top nav by assigning each Jekyll page the correct layout in the page's [front-matter](http://jekyllrb.com/docs/frontmatter/).

```
---
layout: page
title: About
---
```

**Why require a specific layout?** Jekyll will return *all* pages, including the `atom.xml`, and with an alphabetical sort order. To ensure the first link is *Home*, we exclude the `index.html` page from this list by specifying the `page` layout.


## Original Author

[please see hyde repo for more details](https://github.com/poole/hyde)

**Mark Otto**
- <https://github.com/mdo>
- <https://twitter.com/mdo>


## License

Open sourced under the [MIT license](LICENSE.md).

<3
