# How I implemented a dynamic GitHub README.md with GitHub Workflows

Basically I copied [Simon Wilson's](https://github.com/simonw) work, read about it on [his blog
post](https://simonwillison.net/2020/Jul/10/self-updating-profile-readme/).

This is really cool in a couple of ways.

First, GitHub has a feature where if you create a repo with your login
name (i.e. [jchonig/jchong](https://github.com/jchonig/jchonig) it's
special in that the README shows up on your home page.

Second, periodically, or when I push to the repo, GitHub runs my
python script to rebuild my README.md.

Of course, I modified his script.

* I use [jinja2](https://jinja.palletsprojects.com/en/2.11.x/) template as the source of the README.md
* I do a couple different GitHub GraphGL queries, and do them separately.
* I don't have a blog, so I removed that and some other stuff.
