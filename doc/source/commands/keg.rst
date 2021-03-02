keg
===

.. _keg_synopsis:

SYNOPSIS
--------

.. code:: bash

   keg (-r RECIPES_ROOT|--recipes-root=RECIPES_ROOT)
       [-a ADD_DATA_ROOT] ... [-d DEST_DIR] [-fv]
       SOURCE
   keg -h | --help
   keg -h | --help

DESCRIPTION
-----------

Keg is a tool which helps to create and manage image descriptions suitable
for the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder. Its
main use case is to keep control over a larger amount of image descriptions
and prevent duplication of description data.

The key component for Keg is a data structure called `image definition tree`.
This data structure contains all information to create KIWI image
descriptions and provides data in a way that no or as little as possible
duplication exists.

Please find an implementation of an `image definition tree` with
a focus on Public Cloud images here:
`Public Cloud Image Definition Tree <https://github.com/SUSE-Enceladus/keg-recipes>`__

.. _keg_options:

ARGUMENTS
---------

SOURCE

  Path to image source, expected under RECIPES_ROOT/images

OPTIONS
-------

-r RECIPES_ROOT, --recipes-root=RECIPES_ROOT

  Root directory of keg recipes

-a ADD_DATA_ROOT, --add-data-root=ADD_DATA_ROOT

  Additional data root directory of recipes (multiples allowed)

-d DEST_DIR, --dest-dir=DEST_DIR

  Destination directory for generated description, default cwd

-f, --force

  Force mode (ignore errors, overwrite files)

-v, --verbose

  Enable verbose output

EXAMPLE
-------

.. code:: bash

   $ git clone https://github.com/SUSE-Enceladus/keg-recipes.git

   $ keg --recipes-root keg-recipes --dest-dir leap_description leap/jeos/15.2
