.. _recipes_basics:

Recipes basics
==============

To produce image descriptions, `keg` must be provided with source data, also
called `keg recipes`. Unlike `KIWI` descriptions, `keg recipes` can be
composed of an arbitrary number of files, which allows for creating building
blocks for image descriptions. `Keg` does not mandate a specific structure of
the recipes data, with the exception that it expects certain types of source
data in specific directories.

This document describes the fundamental `keg recipes` structure and how `keg`
processes input data to generate an image definition.

Recipes data layout
-------------------

Essentially, a `keg recipes` repository conists of three top-level directories
which contain different types of configuration data. Those three are:

1. Image Definitions: :file:`images`

   The :file:`images` directory contains all image definitions. An image
   defintion specifies the properties and content of the image description to
   generate. Include statements in the image definition allow to reference
   chunks of content from the data modules. Image definitions are specifed in
   YAML format, can be modular and support data inheritence. See
   :ref:`image_definition` for details.

2. Data Modules: :file:`data`

   The :file:`data` directory contains different bits of configuration and
   content data that can be used to compose an image description. There are
   three different types of data modules:

   2.1 Image Definition Modules

   Any directory in :file:`data` that is not file:`scripts` or
   file:`overlayfiles` is considered a module, or module tree, for image
   definition data. Those modules can be referenced in the image definitions
   using `_include` statements. The data is in YAML format and spports
   inheritence.

   2.2 Image Configuration Scriptlets

   Scriptlets can be used to compose optional configuration shell scripts that
   `KIWI` can run during the build process. The scriptlets are located in
   :file:`data/scripts`.

   2.3 Overlay Files

    Image description may include overlay files that get copied into the target
    image. `Keg` can create overlay archives from overlay data directories.
    Overlay files trees are located in :file:`data/overlayfiles`.

  See :ref:`data_modules` for details on data modules.

3. Schema Templates: :file:`schemas`

  `Keg` uses Jinja2 templates to produce the headers for :file:`config.sh`
  and :file:`images.sh`. Both are optional and `keg` will write a fallback
  header if they are missing. Additionally, a Jinja2 template can be used
  to generate :file:`config.kiwi` instead of using the internal XML generator.


Source data format and processing
---------------------------------

This section contains some general information about how `keg` handles its
source data.

An image description is internally represented by a data dictionary with a
certain structure. This dictionary gets composed by parsing source image
definition and data files referenced by the image definition and merging them
into a dictionary.

Image definitions as well as data modules are used by referencing a directory
(under :file:`images` or :file:`data` respectively), which may be several
layers of directories under the root directory. When parsing those, `keg` will
also read any :file:`.yaml` file that is in a directory above the referenced
one, and merge all source data into one dictionary, with the lower (i.e. more
specific) layers taking precedence over upper (i.e. more generic) ones. This
inheritance mechanism is intended to reduce data duplication.

`Keg` uses namespaces in the image definition to group certain bits of
information (for instance, a list of packages) which can be overwritten in
derived modules, allowing for creating specialized versions of data modules
for specific use case or different image description versions.

Once everything is merged, the resulting dictionary is validated against the
image definition schema, to ensure its structure is correct and all required
keys are present. If that is the case, `keg` runs the image dictionary through
its XML generator to produce a `config.kiwi` file. In case the image
definition contains configuration scripts or overlay archives specifications,
`keg` will generate those as well.
