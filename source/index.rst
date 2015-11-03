.. pympi documentation master file, created by
   sphinx-quickstart on Mon Aug  4 11:37:37 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pympi's documentation!
=================================

API Documentation:

.. toctree::
   :maxdepth: 2

   Praat
   Elan

Todo
====
- Elan
- Praat
- General

Old versions
============
- `Version 1.6 <docs_1.6/index.html>`_.
- `Version 1.59 <docs_1.59/index.html>`_.
- `Version 1.5 <docs_1.5/index.html>`_.
- `Version 1.49 <docs_1.49/index.html>`_.
- `Version 1.4 <docs_1.4/index.html>`_.
- `Version 1.39 <docs_1.39/index.html>`_.
- `Version 1.3 <docs_1.3/index.html>`_.
- `Version 1.29 <docs_1.29/index.html>`_.
- `Version 1.2 <docs_1.2/index.html>`_.
- `Version 1.19 <docs_1.19/index.html>`_.
- `Version 1.1 <docs_1.1/index.html>`_.

Changelog
=========
+------------+---------+------------------------------------------------------+
| Date       | Version | Changelog                                            |
+============+=========+======================================================+
| 15-10-26   | 1.69    | - Added get_annotation_before and after functions:   |
|            |         |   :func:`get_annotation_data_after_times`            |
|            |         |   :func:`get_annotation_data_before_times`           |
|            |         |   :func:`get_ref_annotation_data_after_times`        |
|            |         |   :func:`get_ref_annotation_data_before_times`       |
+------------+---------+------------------------------------------------------+
| 15-08-02   | 1.6     | - Tiers are kept in order.                           |
|            |         | - Readme now inline rst.                             |
+------------+---------+------------------------------------------------------+
| 15-07-29   | 1.59    | - Added some ref annotations functions.              |
|            |         | - :func:`get_ref_annotation_data_between_times`      |
|            |         | - :func:`remove_ref_annotation`                      |
|            |         | - :func:`remove_annotation` now also removes ref     |
|            |         |   annotations                                        |
|            |         | - :func:`child_tiers_for` renamed to                 |
|            |         |   :func:`get_child_tiers_for`. Note that the old     |
|            |         |   name is still usable                               |
|            |         | - Reordered the test alphabetically and added tests  |
|            |         |   for the new functions.                             |
+------------+---------+------------------------------------------------------+
| 15-07-27   | 1.5     | - Support for Eaf 2.7                                |
+------------+---------+------------------------------------------------------+
| 15-07-20   | 1.49    | - Fixed unicode bug in Elan for tiernames            |
|            |         | - Added return names in :func:`merge_tier` and       |
|            |         |   :func:`filter_annotations`                         |
|            |         | - Make timeslot parsing and generation more robuust  |
|            |         | - Cleaned up some code                               |
+------------+---------+------------------------------------------------------+
| 15-06-16   | 1.4     | - Fixed unicode bugs in Praat                        |
|            |         | - Removed from/to stream and updated test module     |
|            |         | - Removed read and write from stdin/out in Praat     |
|            |         | - Better python3 code in Praat and refactored tofile |
|            |         | - Made UTF-8 default for Praat reading               |
|            |         | - Fixed a bug in the creation of new textgrids with  |
|            |         |   bounds outside the file                            |
|            |         | - Added option to skip empty annotations in Praat to |
|            |         |   Elan conversion. Note that empty annotations will  |
|            |         |   always be parsed from TextGrid but they are        |
|            |         |   generated just in time for writing. This flag      |
|            |         |   therefore only makes sense when converting         |
|            |         |   textgrids written to disk and read back to elan    |
+------------+---------+------------------------------------------------------+
| 15-03-19   | 1.39    | - Simplified Praat code                              |
|            |         | - Simplified Elan code                               |
+------------+---------+------------------------------------------------------+
| 15-02-05   | 1.3a    | - Fixed a small unicode bug in Elan.py               |
|            |         | - Added information for developing                   |
+------------+---------+------------------------------------------------------+
| 15-01-21   | 1.3     | - Sort tier function for praat tiers                 |
|            |         | - Faster TextGrid constructor with itertools         |
|            |         | - Binary TextGrid support                            |
|            |         | - Short TextGrid support                             |
+------------+---------+------------------------------------------------------+
| 14-11-20   | 1.29    | - Import chat files to elan files.                   |
|            |         | - Added some example scripts that portay possible    |
|            |         |   things you can do with the package and can be used |
|            |         |   as possible templates.                             |
|            |         | - Fixed a non fatal bug about constraints.           |
|            |         | - Internal update for textgrids, tiers don't know    |
|            |         |   their number anymore, numbers are inherited from   |
|            |         |   index in the array.                                |
|            |         | - Python 3 support.                                  |
+------------+---------+------------------------------------------------------+
| 14-11-13   | 1.2     | - Bugfixes.                                          |
|            |         | - Changed the names of the insert functions, the old |
|            |         |   names are still usable. But the preferable method  |
|            |         |   is to use the new functions:                       |
|            |         |   :func:`add_annotation` and                         |
|            |         |   :func:`add_ref_annotation`.                        |
|            |         | - Added controlled vocabulary functions:             |
|            |         |                                                      |
|            |         |   - :func:`add_controlled_vocabulary`                |
|            |         |   - :func:`add_cv_entry`                             |
|            |         |   - :func:`add_cv_description`                       |
|            |         |   - :func:`get_controlled_vocabulary_names`          |
|            |         |   - :func:`get_cv_entries`                           |
|            |         |   - :func:`get_cv_descriptions`                      |
|            |         |   - :func:`remove_controlled_vocabulary`             |
|            |         |   - :func:`remove_cv_entry`                          |
|            |         |   - :func:`remove_cv_description`                    |
|            |         | - Added external reference functions:                |
|            |         |                                                      |
|            |         |   - :func:`add_external_ref`                         |
|            |         |   - :func:`get_external_ref_names`                   |
|            |         |   - :func:`get_external_ref`                         |
|            |         |   - :func:`remove_external_ref`                      |
|            |         | - Added lexicon reference functions:                 |
|            |         |                                                      |
|            |         |   - :func:`add_lexicon_ref`                          |
|            |         |   - :func:`get_lexicon_ref_names`                    |
|            |         |   - :func:`get_lexicon_ref`                          |
|            |         |   - :func:`remove_lexicon_ref`                       |
+------------+---------+------------------------------------------------------+
| 14-11-12   | 1.19    | - Locale functions added: :func:`add_locale`,        |
|            |         |   :func:`remove_locale` and :func:`get_locales`.     |
|            |         | - :func:`add_tier` extended so that you can only     |
|            |         |   assign a locale to a tier when the locale is       |
|            |         |   available, if not no locale will be assigned.      |
|            |         | - Language functions added: :func:`add_language`,    |
|            |         |   :func:`remove_language` and :func:`get_languages`. |
|            |         | - :func:`add_tier` extended so that you can only     |
|            |         |   assign a language to a tier when the language is   |
|            |         |   available, if not no language will be assigned.    |
|            |         | - Property functions added: :func:`add_property`,    |
|            |         |   :func:`remove_property` and                        |
|            |         |   :func:`get_properties`.                            |
|            |         | - Property functions added: :func:`add_license`,     |
|            |         |   :func:`remove_license` and                         |
|            |         |   :func:`get_licenses`.                              |
|            |         | - File io in the elan class is now testable, this    |
|            |         |   will require the lxml library. It uses a sample    |
|            |         |   file that includes almost all data structures      |
|            |         |   possible.                                          |
|            |         | - Added a rename tier function: :func:`rename_tier`. |
|            |         | - Updated how to cite with bibtex.                   |
+------------+---------+------------------------------------------------------+
| 14-10-17   | 1.1a    | - Fixed bugs in ref annotations.                     |
|            |         | - Updated repo description.                          |
+------------+---------+------------------------------------------------------+
| 14-10-17   | 1.1     | - Faster filter_annotions functions                  |
|            |         | - to_textgrid unit test and added regex option       |
|            |         | - Rewritten the gaps and overlaps function, the      |
|            |         |   method is now different, if you want to use the    |
|            |         |   exact heldner and edlund method you can still use  |
|            |         |   :func:`get_gaps_and_overlaps`. If you want to      |
|            |         |   benefit from speed you can use                     |
|            |         |   :func:`get_gaps_and_overlaps2`. They yield almost  |
|            |         |   the same result but the second one is almost 10    |
|            |         |   times faster.                                      |
|            |         | - Added two new functions for adding and viewing     |
|            |         |   secondary linked files:                            |
|            |         |   :func:`get_secondary_linked_files` and             |
|            |         |   :func:`add_secondary_linked_file`.                 |
|            |         | - Added two functions to remove linked files:        |
|            |         |   :func:`remove_linked_files` and                    |
|            |         |   :func:`remove_secondary_linked_files`              |
|            |         | - Added :func:`get_ref_annotation_at_time` for finer |
|            |         |   control over ref annotations.                      |
|            |         | - Adapted :func:`insert_ref_annotation` to work with |
|            |         |   the other ref annotation functions                 |
|            |         | - Adapted :func:`get_ref_annotation_data_for_tier`   |
|            |         |   so that it returns more information, check the     |
|            |         |   documentation for the exact specification.         |
|            |         | - After contact with the elan programmers we've      |
|            |         |   dumbed down the id generation so everything is     |
|            |         |   much faster for big files. Analysis with           |
|            |         |   kcachegrind made everything almost ten times       |
|            |         |   faster.                                            |
|            |         | - Added on how to cite.                              |
|            |         | - Even faster merge tiers.                           |
|            |         | - Used cElementTree instead of ElementTree for more  |
|            |         |   speed.                                             |
|            |         | - Extract function is now also tested.               |
|            |         | - Added safe option for merging and filtering so     |
|            |         |   that if you eaf is malformed by something else     |
|            |         |   because it has zero length annotations then these  |
|            |         |   will be discarded in a merge or filter.            |
+------------+---------+------------------------------------------------------+
| 2014-10-08 | 1.0     | - Glue annotations is removed(you can get the same   |
|            |         |   functionality by using merge tiers.                |
|            |         | - Merge tiers is rewritten and much faster(plans for |
|            |         |   using the same algorithm in the gaps and overlaps. |
|            |         | - Unit tests for all classes.                        |
|            |         | - Reference annotations work but not very usable,    |
|            |         |   this is on the todo list.                          |
|            |         | - Idem for controlled vocabularies.                  |
|            |         | - Shift annotations now returns a tuple of lists     |
|            |         |   instead of an entire eaf object.                   |
|            |         | - get_annotation_datas_between_times is renamed to   |
|            |         |   get_annotation_data_between_times.                 |
|            |         | - Filter annotations now has a regex option.         |
|            |         | - TextGrid constructor now requires xmax for         |
|            |         |   creating a new TextGrid.                           |
|            |         | - Added a parameter dict function for linguistic     |
|            |         |   types.                                             |
|            |         | - Changed the function name: get_linguistic_types to |
|            |         |   get_linguistic_type_names.                         |
|            |         | - Added todo section for list of things that don't   |
|            |         |   have unit tests yet(or incomplete ones) or for     |
|            |         |   things that are to be implemented.                 |
|            |         | - Fixed typo in the to_textgrid function.            |
+------------+---------+------------------------------------------------------+
| 2014-09-26 | 0.99a   | Unit tests for Praat finished and Praat module is on |
|            |         | version 1.0, meaning no api changes in the future    |
|            |         | that break compatibility                             |
+------------+---------+------------------------------------------------------+
| 2014-09-11 | 0.99    | Unit tests for Praat and Elan and from version 1.0   |
|            |         | no api changes.                                      |
+------------+---------+------------------------------------------------------+
| 2014-08-06 | 0.91d   | New documentation format(sphinx) and github pages.   |
+------------+---------+------------------------------------------------------+
| 2014-07-17 | 0.91    | Controlled vocabularies (eaf file format 2.8) added  |
|            |         | and quickly tested.                                  |
+------------+---------+------------------------------------------------------+
| 2014-07-16 | 0.9     | Added support for licences(eaf file format 2.8) and  |
|            |         | planned extended controlled vocabulary support.      |
+------------+---------+------------------------------------------------------+
| 2014-07-09 | 0.7     | Changed the style to pep8 and thus some functions    |
|            |         | (read all) have changed name.                        |
+------------+---------+------------------------------------------------------+
| 2014-03-24 |         | Fixed a lot of TextGrid bugs and have written a      |
|            |         | better parser using more regexp.                     |
+------------+---------+------------------------------------------------------+
| 2014-02-17 |         | Started branching and fixed a few bugs.              |
+------------+---------+------------------------------------------------------+
| 2014-02-03 |         | Fixed the praat tofile function so that it writes    |
|            |         | silence intervals (that praat convention).           |
+------------+---------+------------------------------------------------------+
| 2014-01-27 |         | Added documentation via pdoc in html and cleaned up  |
|            |         | some documentation in EafIO.py.                      |
+------------+---------+------------------------------------------------------+
| 2013-12-02 |         | IO is now in a different file, the old tofile is     |
|            |         | removed because the new one is much better.          |
+------------+---------+------------------------------------------------------+
| 2013-11-15 |         | Rewritten the tofile function, the old function is a |
|            |         | bit faster but less reliable. The old function can   |
|            |         | still be used by using tofileOLD().                  |
+------------+---------+------------------------------------------------------+

Author
======
Mart Lubbers(``mart at martlubbers.net``)

Supervision: Francisco Toreirra(``francisco.torreira at mpi.nl``)
