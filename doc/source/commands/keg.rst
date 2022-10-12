keg
===

.. _keg_synopsis:

SYNOPSIS
--------

**keg** [*options*] <*source*>

DESCRIPTION
-----------

:program:`keg` is a tool which helps to create and manage image descriptions
suitable for the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder.
While :program:`keg` can be used to manage a single image definition the tool
provides no considerable advantage in such a use case. The primary use case for
:program:`keg` are situations where many image descriptions must be managed and
the image descriptions have considerable overlap with respect to content and
setup.

:program:`keg` requires source data called `recipes` which provides all information
necessary for `keg` to create KIWI image descriptions. See
:ref:`recipes_basics` for more information about `recipes`.

The `recipes` used for generating SUSE Public Cloud image descriptions
can be found in the
`Public Cloud Keg Recipes <https://github.com/SUSE-Enceladus/keg-recipes>`__
repository.

.. _keg_options:

ARGUMENTS
---------

source

  Path to image source under RECIPES_ROOT/images

OPTIONS
-------

.. program:: keg

.. option:: -r RECIPES_ROOT, --recipes-root=RECIPES_ROOT

   Root directory of keg recipes. Can be used more than once. Elements
   from later roots may overwrite earlier one.

.. option:: -d DEST_DIR, --dest-dir=DEST_DIR

   Destination directory for generated description [default: .]

.. option:: --disable-multibuild

   Option to disable creation of OBS _multibuild file (for image
   definitions with multiple profiles). [default: false]

.. option:: --disable-root-tar

   Option to disable the creation of root.tar.gz in destination directory.
   If present, an overlay tree will be created instead.
   [default: false]

.. option:: --dump-dict

   Dump generated data dictionary to stdout instead of generating an image
   description. Useful for debugging.

.. option:: -l, --list-recipes

   List available images that can be created with the current recipes

.. option:: -f, --force

   Force mode (ignore errors, overwrite files)

.. option:: --format-yaml

   Format/Update Keg written image description to installed
   KIWI schema and write the result description in YAML markup

   .. note::
      Currently no translation of comment blocks from the Keg
      generated KIWI description to the YAML markup will be
      performed.

.. option:: --format-xml

   Format/Update Keg written image description to installed
   KIWI schema and write the result description in XML markup

   .. note::
      Currently only top-level header comments from the Keg
      written image description will be preserved into the
      formatted/updated KIWI XML file. Inline comments will
      not be preserved.

.. option:: -i IMAGE_VERSION, --image-version=IMAGE_VERSION

   Set image version

.. option:: -a ARCH

   Generate image description for architecture ARCH (can be used
   multiple times)

.. option:: -s, --write-source-info

   Write a file per profile containing a list of all used source
   locations. The files can used to generate a change log from the
   recipes repository commit log.

.. option:: -v, --verbose

   Enable verbose output

.. option:: --version

   Print version


EXAMPLE
-------

.. code:: bash

   git clone https://github.com/SUSE-Enceladus/keg-recipes.git

   keg --recipes-root keg-recipes --dest-dir leap_description leap/jeos/15.2
