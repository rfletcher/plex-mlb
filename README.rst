========
Plex-MLB
========

A Plex_ plugin for mlb.com. Coverage includes video clips, interviews, exclusive stories, as well as live games for MLB.tv subscribers.

Project Status
==============
Development has ceased on this project.  (It was a personal project, and I don't have the time to take on the rewrite required for Plex/Nine compatibility.)  If someone forks and/or gets a Plex/Nine version working, I'll be happy to direct people to your project instead.

Notes for a Potential New Developer
-----------------------------------
The current design gets in the way, and may not work at all with the new version of Plex. I don't suggest trying to build on top of it.  There's probably some useful lower-level code though, especially if you're still trying to figure out where to look on mlb.com for various bits of data.

On top of changes to the plugin API from Plex 8 -> 9, you'll also be dealing with changes to the front and back ends of mlb.com between the 2010 and 2011 seasons.  I'd start by verifying some of the URLs in config.yml.  If they seem to work, then the plugin should still be able to fetch data needed for Plex menus.  At that point I'd dive into the rewrite for Plex/Nine.  Finally, there are probably changes to the MLB media player app, which mean updates to the player.xml "site configuration" file.

There's a passionate bunch of users waiting for you on the Plex forums.  They've been great help testing betas and finding bugs.

------------

Changelog
=========

0.3.2

- new: re-enabled alternate audio streams
- fix: now using MLB's latest player (v4.1)
- fix: fixed game highlights search

0.3.1

- fix: we can now load mlb.com's scoreboard XML, even when it's invalid

0.3

- new: browse and stream archived games
- new: watch condensed games
- new: stream national video broadcasts, if available
- new: stream audio broadcasts
- new: stream mlb.tv "basic" video
- new: watch highlights from a specific game
- new: if a favorite team is selected, jump straight to that team's game with a main menu shortcut
- new: now available as a standalone plugin installer (\*.plexapp)
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
The `Plex-MLB`_ plugin bundle is built from files in the ``bundle/`` and ``templates/`` directories. To build the bundle you'll need:

* Git_
* Ruby_ & Rake_ (Both are bundled with OS X)

With those tools installed, get a copy of the source and install the plugin::

    $ git clone git://github.com/rfletcher/plex-mlb.git
    $ cd plex-mlb
    $ rake install

If you'd like to remove the plugin later, use::

    $ rake uninstall

Or, ``rake uninstall:hard`` to get uninstall the plugin *and* it's preferences and data.

Contributing
============
Code contributions are welcome! If you'd like to add a feature, just fork the
project on GitHub and send me a pull request. Be aware that this is the only
thing I've ever written in Python. If you don't know Python well, don't mimic my
style. If you do, go easy on me (and please do refactor!).

After you've forked `Plex-MLB`_ on GitHub, install the development version of the bundle::

    $ rake install:dev

Plex is now watching ``bundle/`` for changes.  Any edits you make will be automatically loaded by Plex.  Push them up to GitHub and send a pull request.

Links
=====

- Plex_
- `Plex-MLB`_ on GitHub
- `Plex-MLB's page in the Plex Wiki`_

.. _Plex: http://plexapp.com/
.. _`Plex-MLB`: http://github.com/rfletcher/plex-mlb/
.. _`Plex-MLB's page in the Plex Wiki`: http://wiki.plexapp.com/index.php/MLB
.. _Git: http://code.google.com/p/git-osx-installer/downloads/list?can=3
.. _Ruby: http://www.ruby-lang.org/
.. _Rake: http://rake.rubyforge.org/