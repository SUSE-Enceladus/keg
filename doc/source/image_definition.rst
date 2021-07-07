.. _image_definition:

Image Definition
================

`Keg` considers all leaf directories in :file:`images` to be image definitions.
This means by parsing any yaml file from those directories and all yaml files
in any parent directory and merging their data into a dictionary, a complete
image definition needs to be available in the resulting dictionary. There is no
specific hierarchy required in :file:`images`. You can use any level of sub
directories to use any level of inheritance, or simply just to group image
definitions. Example directory layout::

  images/
         opensuse/
                  defaults.yaml
                  leap/
                       profiles.yaml
                       15.2/
                            image.yaml
                       15.3/
                            image.yaml

This example layout defines two images, `opensuse/leap/15.2` and
`opensuse/leap/15.3`. It uses inheritence to define a common profile for both
image definitions, and to set some `opensuse` specific defaults. Running `keg
-d output_dir opensuse/leap/15.3` would merge data from the following files in
the show order::

  images/opensuse/defaults.yaml
  images/opensuse/leap/profiles.yaml
  images/opensuse/leap/15.3/image.yaml

Image Definition Structure
--------------------------

To properly define an image, the dictionary produced from merging the
dictionaries from a given input path need to have the following structure:

.. code:: yaml

  archs:
    - string
    ...
  include-paths:
    - string
    ...
  image:
    author: string
    contact: string
    name: string
    specification: string
    version: integer.integer.integer
  profiles:
    common:
      include:
        - string
        ...
    profile1:
      include:
        - string
        ...
    ...
  schema: string
  users:
    - name: string
      groups:
        - string
        ...
      home: string
      password: string
    ...


.. note::

  `schema` corresponds to a template file in :file:`schema` (with
  ``.kiwi.templ`` extension added). The schema defines the output structure and
  hence the input structure is dependent on what schema is used.

  Some of the listed dictionary items are not strictly required by keg but
  they are used by the template provided in the `keg-recipes repository
  <https://github.com/SUSE-Enceladus/keg-recipes>`__.

.. note::

  Image definitions that define a `common` profile only in the `profiles`
  section are considered single-build and definitions with additional
  profiles are considered multi-build. Again, this depends on the used
  template and may not be true for custom templates.

The `profiles` section is what defines the image configuration and data
composition. Any list item in `include` refers to a directory under
:file:`data`.
