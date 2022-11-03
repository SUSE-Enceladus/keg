.. _changelog_generator:

Generating change logs
======================

`Keg` comes with a separate tool that can be used to produce a change log
for a generated image description from the git commit history of the used
`keg recipes` tree(s). This obviously requires these `keg recipes` to be
stored in git repositories.

To produce a change log for an image description, the description needs to
be generated with source info tracking enabled in :program:`keg` (`-s` command
line switch).

Source info tracking
--------------------

With source info tracking enabled, `keg` will write one or more source info
files in addition to the image description in the output directory. In case
the image description at hand is single-build, a single file
:file:`log_sources` is written, in case it is multi-build, a file
:file:`log_sources_PROFILE` is written for each profile. This allows for
generating individual change logs for the resulting image binaries.

The source info logs contain detailed information about which bits from the
`keg-recipes` tree was used to generate the image description. The source
info log files will contain several lines of the following format:

.. code:: bash

  root:/path/to/repository
  range:start:end:/path/to/repository/file
  /path/to/repository/file_or_dir

The first line specifies the repository location. There will be one for
each `keg-recipes` directory given to `keg`. Lines starting with `range:`
specify a part of a file in a repository. This is used to track the source
location of each key that was in the final image dictionary. The third
line format simply specifies a file or a directory in the repository that
was used in the image description, and is used for configuration script
snippets and overlay files.

This enables the change log generator to produce a change log using the
git commit history, selecting only commits that apply to the generated
image description.

Change log generator
--------------------

The generated source info log files, together with the `keg-recipes`
in the place and state they were used to generate the image description,
can be used to generate change logs. The `keg` distribution contains
a tool :program:`generate_recipes_changelog` for that purpose. When called
with a source log file as argument, :program:`generate_recipes_changelog`
will use the source information to select matching git messages and
produce a change log in chronological order. There are parameters to
to narrow down the applicable commit range as well as some formatting
options. Refer to :ref:`generate_recipes_changelog` command overview
for details.

Integration in OBS source service
---------------------------------

The `keg` distribution contains a module for integrating with the Open Build
Service, an implementation of a so-called `OBS Source Service
<https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.source_service.html>`_.
It supports automatic handling of change log generation. See :ref:`Keg OBS
Source Service <keg_obs_source_service>` for details.
