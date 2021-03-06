Stackalytics
============

Application Features
--------------------
Stackalytics is a service that automatically analyzes OpenStack
development activities and displays statistics on contribution. The features are:
 * Extraction of author information from git log, store it in the database;
 * Calculate metrics on number of lines changed (LOC) and commits;
 * Mapping authors to companies and launchpad ids;
 * Filter statistics by time, modules, companies, authors;
 * Extract blueprint and bug ids from commit messages;
 * Auto-update of database.

Project Info
-------------

 * Web-site: http://stackalytics.com/
 * Source Code: http://git.openstack.org/cgit/stackforge/stackalytics
 * Wiki: https://wiki.openstack.org/wiki/Stackalytics
 * Launchpad: https://launchpad.net/stackalytics
 * Blueprints: https://blueprints.launchpad.net/stackalytics
 * Bugs: https://bugs.launchpad.net/stackalytics
 * Code Reviews: https://review.openstack.org/#q,status:open+stackalytics,n,z
 * IRC: #openstack-stackalytics at freenode

Blueprint: Add translation metric
--------------
Back end tasks
 * Return a fack translation record
 * Read translation_team.yaml(main.py)
 * Read project list from Zanata(tls.py)
 * Read translator record from Zanata(tls.py)
 * Insert translation data into record (record_processor.py)


