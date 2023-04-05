.. _image_definition:

Image definition
================

In `keg` terminology, an image definition is the data set that specifies the
KIWI image description that should be generated. `keg` reads image definition
from the `images` directory in the `recipes` root directory.

`Keg` considers all leaf directories in :file:`images` to be image definitions.
This means by parsing any YAML file from those directories and all YAML files
in any parent directory and merging their data into a dictionary, a complete
image definition needs to be available in the resulting dictionary. There is no
specific hierarchy required in :file:`images`. Any level of sub directories can
be used to create multiple levels of inheritance, or simply just to group image
definitions. Example directory layout::

  images/
         opensuse/
                  defaults.yaml
                  leap/
                       content.yaml
                       15.2/
                            image.yaml
                       15.3/
                            image.yaml

This example layout defines two images, `opensuse/leap/15.2` and
`opensuse/leap/15.3`. It uses inheritance to define a common content
definition for both image definitions, and to set some `opensuse` specific
defaults. Running :command:`keg -d output_dir opensuse/leap/15.3` would merge
data from the following files in the show order::

  images/opensuse/defaults.yaml
  images/opensuse/leap/content.yaml
  images/opensuse/leap/15.3/image.yaml

All keys from the individual YAML files that are in the given tree will be
merged into a dictionary that defines the image to be generated.


Image definition structure
--------------------------

An image definition dictionary is composed of several parts that define
different parts of the image. The actual image description, configuration
scripts, overlay archives. All parts are defined under a top-level key
in the dictionary. There are additional top-level keys that affect data
parsing and generator selection.

The top-level keys are as follows:

image
^^^^^

The image dictionary. This is the only mandatory top-level key. It defines
the content of the :file:`config.kiwi` file `keg` should generate and is
essentially a YAML version of `KIWI's` image description (typically in XML). It
contains all image configuration properties, package lists, and references to
overlay archives. There is a number of special keys that influence how `keg`
constructs the dictionary and generates the XML output. The basic structure is
as follows:

.. code:: yaml

  image:
    _attributes:
      schemaversion: "<schema_maj>.<schema_min>"
      name: <image_name>
      displayname: <image_boot_title>
    description:
      _attributes:
        type: <system_type>
      author: <author_name>
      contact: <author_email>
    preferences:
      - version: <version_string>
      - _attributes:
          profiles:
            - <profile_name>
            ...
        type:
          _attributes:
            image: <image_type>
              kernelcmdline:
              <kernel_param>: <kernel_param_value>
              ...
            ...
          size:
            _attributes:
              unit: <size_unit>
            _text: <disk_size>
      ...
    users:
      user:
        - _attributes:
            name: <user_name>
            groups: <user_groups>
            home: <user_home>
            password: <user_password>
	...
    packages:
      - _attributes:
          type: image|bootstrap
          profiles:
            - <profile>
	    ...
        archive:
          _attributes:
            name: <archive_filename>
        <namespace>:
          package:
            - _attributes:
                name: <package_name>
                arch: <package_arch>
	    ...
        ...
      ...
    profiles:
      profile:
        - _attributes:
            name: <profile_name>
            description: <profile_description>
        ...

This only outlines the structure and includes some of the configuration keys
that `KIWI` supports. See `KIWI Image Description
<https://documentation.suse.com/kiwi/9/single-html/kiwi/index.html#image-description>`_
for full details.

For the purpose of generating the `KIWI` XML image description, any key in the
`image` dictionary that is not a plain data type is converted to an XML element
in the `KIWI` image description, with the tag name being the key name. Any key
that starts with an `_` has a special meaning. The following are supported:

  `_attributes`

If a key contains a sub key called `_attributes`, it instructs the XML
generator to produce an attribute for the XML element  with the given key name
and value as its name-value pair. If value is not a plain data type, it is
converted to a string, which allows for complex attributes being split over
different files and also for redefinition on lower levels. For example:

.. code:: yaml

  type:
    _attributes:
      image: vmx
      kernelcmdline:
        console: ttyS0
        debug: []

Would generate the following XML element:

.. code:: xml

  <type image="vmx" kernelcmdline="console=ttyS0 debug"/>

The empty list used as value for `debug` means the attribute parameter is
valueless (i.e. a flag).

  `_text`

If a key contains a key called `_text`, its value is considered the element's
content string.

  `_namespace[_name]`

Any key that start with `_namespace` does not produce an XML element in the
output. Namespaces are used to group data and allow for an inheritance and
overwrite mechanism. Namespaces produce comments in the XML output that
states which namespace the enclosed data was part of.

  `_map_attribute`

If a key contains a key `_map_attribute`, which needs to be a string type,
any `_attribute` key under the key that is a simple list instead of the
actually required mapping, is automatically converted to a mapping with the
attribute key equal to `_map_attribute` value. For example:

.. code:: yaml

  packages:
    _map_attribute: name
    _namespace_some_pkgs:
      package:
        - pkg1
        - pkg2

Is automatically converted to:

.. code:: yaml

  packages:
    _namespace_some_pkgs:
    package:
      - _attribute:
          name: pkg1
      - _attribute:
          name: pkg1
    archive:
      - _attributes:
          name: archive1.tar.gz

This allows for making lists of elements that all have the same attribute
(which package lists typically have) more compact and readable.


  `_comment[_name]`

Any key that has a key that starts with `_comment` will have a comment above
it in the XML output, reading the value of the `_comment` key (needs to be
a string).


.. _imgdef_config:

config
^^^^^^

The config dictionary defines the content of the :file:`config.sh` file `keg`
should generate. :file:`config.sh` is a script that `KIWI` runs during the image
prepare step and can be used to modify the image's configuration. The
:file:`config` dictionary structure is as follows:

.. code:: yaml

  config:
    - profiles:
        - <profile_name>
        ...
      files:
        <namespace>:
          - path: <file>
            append: bool (defaults to False if missing)
            content: string
          ...
	...
      scripts:
        <namespace>:
          - <script>
          ...
	...
      services:
        <namespace>:
          - <service_name>
          - name: <service_name>
            enable: bool
	  ...
	...
      sysconfig:
        <namespace>:
          - file: <sysconfig_file>
            name: <sysconfig_variable>
            value: string
	  ...
	...
    ...

Each list item in `config` produces a section in :file:`config.sh`, with the
optional `profiles` key defining for which image profile that section should
apply. Each item can have the following keys (all are optional, but there has
to be at least one):

`files` defines files that should be created (or overwritten if existing) with
the given `content` or have `content` appended to in :file:`config.sh`.

`scripts` defines which scriptlets should be included. `<script>` refers to
a file :file:`data/scripts/<script>.sh` in the recipes tree.

`services` defines which systemd services and timers should be enabled or
disabled in the image. The short version (just a string) means the
string is the service name and it should be enabled.

`sysconfig` defines which existing sysconfig variables should the altered.

.. note::

  `<namespace>` defines a namespace with the same purpose as in the `image`
  dictionary, but `config` namespaces don't have to start with `_`, but are
  allowed to.

setup
^^^^^

The config dictionary defines the content of the :file:`images.sh` file `keg`
should generate. This script is run by `KIWI` during the image create step. Its
structure is identical to `config`.

See `User defined scripts
<https://documentation.suse.com/kiwi/9/single-html/kiwi/index.html#working-with-kiwi-user-defined-scripts>`__
in the `KIWI` documentation for more details on user scripts.


.. _imgdef_archive:

archive
^^^^^^^

The archive dictionary defines the content of overlay tar archives, that can be
included in the image via the `archive` sub-section of the `packages` section
of the `image` dictionary. The structure is as follows:

.. code:: yaml

  archive:
    - name: <archive_filename>
      <namespace>:
        _include_overlays:
          - <overlay_module>
          ...
    ...

When generating the image description, `keg` will produce a tar archive for
each entry in `archive` with the given file name, with its contents being
composed of all files that are in the listed overlay modules. Each module
references a directory in :file:`data/overlayfiles`.

`Keg` automatically compresses the archive based on the file name extension.
Supported are `gz`, `bz2`, `xz`, or no extension for uncompressed archive.

.. note::

  The archive name `root.tar` (regardless of compression extension) is
  automatically included in all profiles (if there are any) by `KIWI`.
  It is not necessary to include it explicitly in the image definition.


The _include statement
----------------------

`Keg` supports importing parts of the image definition from other directory
trees within the recipes to allow for modularization. For that purpose, a key
in the image dictionary may have a sub-key called `_include`. Its value is a
list of strings, each of which points to a directory in the `data`
sub-directory of the recipes root. To process the instruction, `keg` generates
another dictionary from all YAML files in the referenced directory trees (the
same mechanism as when parsing the `images` tree applies). It then looks up the
key in that dictionary that is equal to the parent key of the `_include` key,
and replaces the `_include` key with its contents. That means, if the
`_include` statement is below a key called `packages`, only data under
`packages` in the include dictionary will be copied into the image definition
dictionary. This allows for having different types of configuration data in the
same directory and including them in different places in the image definition.
See :ref:`data_modules` for details on data modules.

Additional configuration directives
-----------------------------------

There are three additional optional top-level image definition sections that
affect how the image definition dictionary is composed and the image
description is generated:

include-paths
^^^^^^^^^^^^^

The `include-paths` key defines a list of search paths that get appended 
when `_include` statements are processed. This allows for having different
versions of data modules and still share the most of an image definition
between different versions. See :ref:`data_modules` for details.

image-config-comments
^^^^^^^^^^^^^^^^^^^^^

This section allows to add top-level comments in the produced `KIWI` file.
The format is as follows:

.. code:: yaml

  image-config-comments:
    <comment_name>: <comment>
    ...

`<comment_name>` is just a name and is not included in the generated output.
Comments can be used to include arbitrary information in the image description.
Some comments have a special meaning for processing image descriptions by the
Open Build Service, for instance the `OBS-Profiles` directive that is required
to process multi-profile image descriptions. See
`<https://osinside.github.io/kiwi/working_with_images/build_in_buildservice.html>`__
for details.

.. note::

  Keg generates some comments automatically. In case the image definition has
  multiple profiles and the `--disable-multibuild` command line switch is not
  set, it will add an `OBS-Profiles: @BUILD_FLAVOR@` comment. In case the
  image description is generated for one or more specific architectures
  via the `-a` command line option, the apprpriate `OBS-ExclusiveArch`
  comment is added.


xmlfiles
^^^^^^^^

This optional section allows generating additional custom XML files. The format
is as follows:

.. code:: yaml

  xmlfiles:
    - name: <filename>
      content:
        <content_dictionary>
    ...

For each list item in this section, an XML file named :file:`<filename>` will
be created, with the content being generated from the `<content_dictionary>`.
For this dictionary the same rules about formatting, including, namespacing,
etc., apply as for the image dictionary.

Custom XML files can be useful when generating image descriptions for use in
the Open Build Service, which accepts build configuration directives via XML
source files, like the :file:`_constraints` file. See
`<https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.build_job_constraints.html>`__
for details.

schema
^^^^^^

`Keg` starting with version 2.0.0 has an internal XML generator to produce
`KIWI` image descriptions. Previously, a Jinja2 template was used to convert
the image dictionary that `keg` constructed into a `KIWI` image description.
Using a Jinja2 template is still supported and can be configured as follows
in the image definition:

.. code:: yaml

  schema: <template>

In this case, instead of running the XML generator, `keg` would read the
file :file:`<template>.kiwi.templ` from the `schemas` directory in the recipes
root directory and run it trough the Jinja2 engine.

.. note::

  While using a Jinja2 template would in theory allow to operate on different
  input data structures, the internal schema validator requires the image
  definition to comply with what `keg` expects.
