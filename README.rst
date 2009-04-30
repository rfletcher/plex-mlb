========
Plex-MLB
========

`Plex-MLB`_ lets you watch video from mlb.com in Plex_.

Changelog
=========

Upcoming

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

Roadmap/Wishlist
================

0.2

- Time zone awareness
- Caching!

0.3

- Allow choice of home or away video feeds for MLB.tv streams
- Live game audio streaming for Gameday Audio and MLB.tv subscribers

TBD

- Access archived MLB.tv and Gameday content
- Support for advanced features of the MLB.tv player (picture-in-picture & other views, etc.)

Building From Source
====================
The `Plex-MLB`_ plugin bundle is built from files in the ``src/`` directory.
To build the bundle you'll need:

* Git_
* Ruby_ & Rake_ (Both are bundled with OS X)

Once you've got all those installed, get a copy of the source, and install the plugin::

    $ git clone git://github.com/rfletcher/plex-mlb.git
    $ cd plex-mlb
    $ rake install

Note that this installs a development version of the plugin, which won't be auto-updated by the App Store, for example.

If you'd like to remove the plugin later, use::

    $ rake uninstall

Links
=====

- Plex_
- `Plex-MLB's page in the Plex Wiki`_

.. _Plex: http://plexapp.com/
.. _`Plex-MLB`: http://github.com/rfletcher/plex-mlb/
.. _`Plex-MLB's page in the Plex Wiki`: http://wiki.plexapp.com/index.php/MLB
.. _Git: http://git-scm.com/
.. _Ruby: http://www.ruby-lang.org/
.. _Rake: http://rake.rubyforge.org/
.. _RubyGems: http://rubygems.org/
.. _`libxml-ruby`: http://libxml.rubyforge.org/