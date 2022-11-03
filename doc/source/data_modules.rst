.. _data_modules:

Data modules
============

Data modules are essentially directories in the :file:`data` tree. There are
three different kinds of data modules:

1. Image Definition Modules

  Any part of the image definition can be in a data module that is
  included by the `_include` statement from the main image definition.

2. Image Configuration Scriptlets

  Configuration scriptlets are stored in :file:`data/scripts`.
  Those scriptlets can be used to compose an image configuration script or
  image setup script `config` and `setup` key in the image definition.

3. Overlay Files

  Files that can be directly included in the image description and will be
  copied into the image's file system by `KIWI` during the build process.
  Overlay files are stored under :file:`data/overlayfiles`.


Image definition modules
------------------------

Any directory under :file:`data` that is not `scripts` or `overlayfiles`
is considered an image definition data module and may be included in the
main image definition using the `_include` statement.

Inheritance rules apply similarly to the image definition tree, but
additionally, `keg` supports sub-versions of data modules. This can be used for
instance to create slightly different versions of modules for use with
different image versions while still sharing most of the image definition
between those versions.

For this purpose, `keg` supports the `include-paths` directive in the image
definition. Include paths are paths that get appended to any source path and
those get scanned for input files as well. See the following image definition
as an example:

.. code:: yaml

  include-paths:
    leap15/1
    leap15/2
  image:
    preferences:
      - _include:
          - base/common
    packages:
      - _include:
          - base/common
    config:
      - _include:
          - base/common


This tells `keg`, when adding data from directory :file:`data/base/common` to
the image data dictionary, to also look into sub directories :file:`leap15/2`,
:file:`leap15/1`, and :file:`leap15` (through inheritance). This would lead to
the following directories being scanned::

  data
  data/common
  data/common/base
  data/common/base/leap15
  data/common/base/leap15/1
  data/common/base/leap15/2

This allows for example to put generic configuration bits in
:file:`data/common/base`, Leap 15 specific configuration in
:file:`data/common/base/leap15`, and adjust the configuration for minor
versions, if necessary.

When merging the included dictionaries into the main dictionary, `keg` only
copies the dictionary under the top level key that matches the key under
which the `_include` statement is. That means, assuming the YAML files
collected from the above trees resulted in the following data structure:

.. code:: yaml

  preferences:
    locale: en_US
    timezone: UTC
    type:
      _attributes:
        firmware: efi
        image: vmx
  packages:
    _namespace_base_packages:
      package:
        - bash
        - glibc
        - kernel-default
  config:
    _namespace_base_services:
      services:
        - sshd

Would result in a data structure like this:

.. code:: yaml

  include-paths:
    leap15/1
    leap15/2
  image:
    preferences:
      locale: en_US
      timezone: UTC
      type:
        _attributes:
          firmware: efi
          image: vmx
    packages:
      _namespace_base_packages:
        package:
          - bash
          - glibc
          - kernel-default
  config:
    _namespace_base_services:
      services:
        - sshd


Merging based on the parent key allows for grouping of different types of
configuration data in one data module.


Image configuration scriptlets
------------------------------

Configuration scriptlets are individual script snippets that can be used
to generate image configuration scripts. `KIWI` runs those scripts at
certain points in the image build process. They can be used to do changes
to the system's configuration.

The scriptlets are located in :file:`data/scripts` and are required to have a
:file:`.sh` suffix. These are referenced in the `scripts` lists of the `config`
or `setup` sections in the image definition (without the :file:`.sh` suffix). 
See :ref:`imgdef_config` for details on the `config` section.

Overlay files
-------------

`KIWI` image descriptions can contain optional overlay archives, which will be
extracted into the system's root directory before the image is created.
Overlay files are located in sub-directories in :file:`data/overlayfiles`,
with each sub-directory representing an overlay files module. Any directory
structure under the module's top directory is preserved.

Overlay files modules can be referenced in the `archive` section of the image
definition using the `_include_overlays` directive. See :ref:`imgdef_archive` for
details.
