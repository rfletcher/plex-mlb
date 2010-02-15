========
Plex-MLB
========

`Plex-MLB`_ lets you watch video from mlb.com in Plex_.

Changelog
=========

0.3beta1

- new: now available as a standalone plugin installer (*.plexapp)
- new: added preference for streaming your favorite team's broadcast, even when they're on the road
- fix: fixed a number of highlight searching/listing bugs stemming from changes to the mlb.com backend

0.2

- new: added live game streaming for MLB.tv subscribers
- new: added shortcuts to some of mlb.com's better daily highlights (FastCast, MLB Network, Plays of the Day)
- new: added preference for favorite team
- new: added preference to show/hide spoilers (default: show)
- change: removed "popular searches", since it is no longer being updated by mlb.com
- fix: fixed team highlights, broken due to a change on mlb.com

0.1.1

- fix: team, popular and search pages now display current team, keyword or query instead of the word "Search" in the page title
- new: added standard search icon

0.1

- new: initial version
- new: search/browse video clips from mlb.com

Building From Source
====================
The `Plex-MLB`_ plugin bundle is built from files in the ``src/`` directory.
To build the bundle you'll need:

* Git_
* Ruby_ & Rake_ (Both are bundled with OS X)

With those tools installed, get a copy of the source and install the plugin::

    $ git clone git://github.com/rfletcher/plex-mlb.git
    $ cd plex-mlb
    $ rake install:dev

Note that this installs a development version of the plugin, which won't be auto-updated by the App Store, for example.

If you'd like to remove the plugin later, use::

    $ rake uninstall

Contributing
============
Code contributions are welcome! If you'd like to add a feature, just fork the
project on GitHub and send me a pull request. Be aware that this is the only
thing I've ever written in Python. If you don't know Python well, don't mimic my
style. If you do, go easy on me (and please do refactor!).

Links
=====

- Plex_
- `Plex-MLB's page in the Plex Wiki`_

.. _Plex: http://plexapp.com/
.. _`Plex-MLB`: http://github.com/rfletcher/plex-mlb/
.. _`Plex-MLB's page in the Plex Wiki`: http://wiki.plexapp.com/index.php/MLB
.. _Git: http://code.google.com/p/git-osx-installer/downloads/list?can=3
.. _Ruby: http://www.ruby-lang.org/
.. _Rake: http://rake.rubyforge.org/