# Work in progress! 

- the contents of this webpage can easily be updated using markdown language.


## Contents

- [Work in progress!](#work-in-progress)
  - [Contents](#contents)
    - [Added Top menu](#added-top-menu)
  - [Original Author:](#original-author)
  - [License](#license)


### Added Top menu

Create a list of nav links in the top nav by assigning each Jekyll page the correct layout in the page's [front-matter](http://jekyllrb.com/docs/frontmatter/).

```
---
layout: page
title: About
---
```

**Why require a specific layout?** Jekyll will return *all* pages, including the `atom.xml`, and with an alphabetical sort order. To ensure the first link is *Home*, we exclude the `index.html` page from this list by specifying the `page` layout.


## Original Author:

[please see hyde repo for more details](https://github.com/poole/hyde)

**Mark Otto**
- <https://github.com/mdo>
- <https://twitter.com/mdo>


## License

Open sourced under the [MIT license](LICENSE.md).

<3
