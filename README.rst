========
Plex-MLB
========

`Plex-MLB`_ lets you watch video from `mlb.com`_ with `Plex Media Server`_.

To Do
=====
- (0.2) Add live game video streaming for MLB.tv subscribers
- (0.3) Add live game audio streaming for Gameday Audio and MLB.tv subscribers

Changelog
=========

HEAD

- new: added preference for favorite team
- change: removed "popular searches", since it is no longer being updated by mlb.com
- fix: fixed team highlights, broken due to a change on mlb.com

0.1.1

- fix: team, popular and search pages now display current team, keyword or query instead of the word "Search" in the page title
- new: added standard search icon

0.1

- new: initial version
- new: search/browse clips from `mlb.com`_

Building From Source
====================
The `Plex Media Server` plugin bundle is built from files in the ``src/`` directory.
To build the bundle you'll need:

* A copy of the `Plex-MLB` source tree
* Ruby_ & Rake_

From the root `Plex-MLB` directory, run:

* ``rake dist`` to generate the .bundle and site config xml file (both will be placed in ``dist/``)
* ``rake package`` to create a distribution tarball from files in ``dist/`` and place it in the ``pkg/`` directory
* Alternatively, ``rake`` alone will run both ``rake dist`` and ``rake package``

If you're making changes to the plugin and would like to install your updates locally:

* ``rake install`` will generate an updated .bundle and site config XML, and install them both in the appropriate place beneath ``~/Library/Application Support/Plex Media Server``

Links
=====

- `Plex Media Server`_
- `Plex-MLB's page in the Plex Wiki`_

.. _`Plex-MLB`: http://github.com/rfletcher/plex-mlb/
.. _`Plex-MLB's page in the Plex Wiki`: http://wiki.plexapp.com/index.php/MLB
.. _`Plex Media Server`: http://plexapp.com/
.. _`mlb.com`: http://mlb.mlb.com/media/video.jsp
.. _Ruby: http://www.ruby-lang.org/
.. _Rake: http://rake.rubyforge.org/