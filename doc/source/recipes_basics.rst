.. _recipes_basics:

Recipes Basics
==============

To produce image descriptions, keg must be provided with source data, also
called `keg recipes`. Unlike kiwi descriptions, keg recipes can be composed of
an arbitrary number of files, which allows to create building blocks for
images. Keg does not mandate a specific structure of the recipes data, with the
exception that it expects certain types of source data in specific directories,
but how you want to structure the data is up to you.

This document describes the fundamental `keg recipes` structure and how `keg`
processes input data to generate an image definition.

Recipes Data Types
------------------

There are several types of source data in `keg recipes`:

1. Image Definitions

  Defines image properties and composition. Image definitions must be placed in
  the :file:`images` directory in the recipes root directory. Input format is
  `yaml`.

  See :ref:`image_definition` for details.

2. Data Specifications

  Specifies profile paramaters, package lists, image setup configuration, and
  overlay data configuation. Data specifications must be placed in the
  :file:`data` directory. The sub directories :file:`data/scripts` and
  :file:`data/overlayfiles` are reserved for configuration scriptlets and
  overlay files (see below). Everything else under :file:`data` is considered
  data module specficiation with input format `yaml`.

  2.1 Image Configuration Scripts

    Image descriptions may include configuration scripts, which `keg` can compose
    from scriptlets. Those must be placed in :file:`data/scripts`. All files
    need to have a `.sh` suffix. Format is `bash`.

  2.2 Overlay Data

    Image description may include overlay files that get copied into the target
    image. `Keg` can create overlay archives from overlay data directories.
    Those must be placed in :file:`data/overlayfiles`.

  See :ref:`data_modules` for details on data modules.

3. Schema Templates

  `Keg` uses `jinja2` templates to produce the target `config.kiwi` file. The
  template defines the output structure, which is provided with the full image
  description as composed by `keg`. Templates need to be in :file:`data/schemas`.

Source Data Format and Processing
---------------------------------

This section contains some general information about how `keg` handles its
source data. An image description is internally represented by a data
dictionary with a certain structure. This dictionary gets composed by parsing
source image definition and data files referenced by the image definition
and merging them into a dictionary. Image defintions as well as data modules
are used by referencing a directory (under :file:`images` or :file:`data`
respectively), which may be several layers of directories under the root
directory. When parsing those, `keg` will also read any yaml file that is
in a directory above the referenced one, and merge all source data into
one dictionary, with the lower (i.e. more specific) layers taking precedence
over upper (i.e. more generic) ones. This inheritance mechanism is intended to
reduce data duplication.
