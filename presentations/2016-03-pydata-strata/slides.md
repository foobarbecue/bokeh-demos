# Intro to data visualization with Bokeh

## PyData at Strata

- Sarah Bird [@birdsarah](https://twitter.com/birdsarah)
- Bryan Van de Ven [@bryvdv](https://twitter.com/bryvdv)

http://github.com/bokeh/bokeh-demos/

<small>March 29th, 2016</small>

Note:
- Don't worry about the styling, once the content's in place, I'll give it a skin - probably simple and similar to https://birdsarah.github.io/europython-2015-bokeh/static/slides.html#/2 with an extra corner logo
- I'm thinking we put a link on this home screen to where people can get lots of links and refs for the fist half, and then we put up a link over lunch for getting the tutorial

---

## Overview

- 11:30 - 12:30 Intro to Bokeh ecosystem (code-along)
- 12:30 - 13:30 LUNCH
- 13:30 - 14:30 Hands-on examples (tutorials or bring your own data)

---

## Getting set-up

- In order of simplicity:
 - Anaconda https://www.continuum.io/downloads
 - **Miniconda http://conda.pydata.org/miniconda.html (my personal preference)**
   
    `conda install bokeh`

 - Pip (can take a long time due to dependencies)

      `pip install bokeh`

***You don't need to do this now, we will be available to help duing lunch, so you're ready for the tutorials***

---

## Bokeh

<img class="slide_image" src="images/gallery-screenshot.png" style="position: absolute; top: 0; right: 0; opacity: 0.2">

- data visualization library
- web-based, interactive, data-driven
 - no javascript required
- can handle large-data, streaming-data, dynamic-data

<br/>

## Growing eco-system

---

## Bokeh - Core

- Python-based - http://bokeh.pydata.org
- Charts (Bar chart, Histogram...)
- Custom plots
- User interactions & styling
- Server interactions


---

## Bokeh - Ecosystem

- Other language bindings: rbokeh (actively maintained), scala (activeley maintained), julia (not maintained), typescript (coming soon)
- Datashader - interact with BIG<sup>**</sup> data
- Write your own custom models

---

## Core concepts for today

- Navigating Bokeh's interfaces 
 - charts, plotting, and probably not models!
- Bokeh server 
 - what it is, what it isn't, do I need it
- Sharing your work 
 - notebook, standalone files, server 
- Awareness of the Bokeh ecosystem

---

## Interfaces

There are a number of ways to use Bokeh - pick the one that's right for you:

* Charts (high speed)
* Plotting (sensible defaults)
* Models (high customization)

We'll come back to this multiple times today.

---

<h5 style="padding-top: 1em; margin-bottom: -0.2em"> `bokeh.charts` (high speed)</h5>

- One-line charts
- Processes your data & spits out a chart


<h5 style="padding-top: 1em; margin-bottom: -0.2em"> `bokeh.plotting` (sensible defaults)</h5>

- Tries to pick sensible defaults
- You organize your data, it organizes your plot

<h5 style="padding-top: 1em; margin-bottom: -0.2em"> `bokeh.models` (high customization)</h5>

- The lowest level
- Offers you the most control
- Do all the work yourself

---

## Interfaces

* Charts (high speed)
* Plotting (sensible defaults)
* Models (high customization)

We'll come back to this multiple times today.

---

## Bokeh Server

- deep interactivity
- streaming data

---

# Appendix

---

## Hacker-slides how-to

- Separate slides using '`---`' on a blank line
- Write github flavored markdown
- Click 'Present' (top right) when you're ready to talk
- There is also a speaker view, with notes - press '`s`'
- Press '`?`' with focus on the presentation for shortcuts
- <em>You can use html when necessary</em>
- Share the 'Present' URL with anyone you like!

Learn more:
- [RevealJS Demo/Manual](http://lab.hakim.se/reveal-js)
- [RevealJS Project/README](https://github.com/hakimel/reveal.js)
- [GitHub Flavored Markdown](https://help.github.com/articles/github-flavored-markdown)

Note:
- Anything after `Note:` will only appear here
