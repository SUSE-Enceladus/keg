.. _data_modules:

Data Modules
============

Data modules are essentially directories in the :file:`data` tree. Inheritence
rules apply similarly to the image definition tree, but additionally, `keg`
supports cross inheritance for data modules. Cross inheritance is useful to
inherit configuration changes from previous version. This can be specified in
the image definition using the `include-paths` list. Include paths are paths
the get appended to any source path and those get scanned for input files as
well. For example, let's assume you have the following configration in your
image defintion:

.. code:: yaml

  include-paths:
    leap15/1
    leap15/2
  profiles:
    common:
      include:
        base/common


This tells `keg`, when adding data from directory :file:`data/base/common` to
the image data dictionary, to also look into sub directories :file:`leap15/2`,
:file:`leap15/1`, and :file:`leap15` (through inheritance). This would lead to
the following directories being scanned::

  data/common
  data/common/base
  data/common/base/leap15
  data/common/base/leap15/1
  data/common/base/leap15/2

This allows for example to put generic configuration bits in
:file:`common/base`, Leap 15 specific configuration in
:file:`common/base/leap15`, and adjust the configuration for minor versions, if
necessary.

When building the dictionary, `keg` will parse all input files referenced
in the `profiles` section and merge them into the main dictionary. The
folliwing section describes the structure used in the data section.


Data Module Dictionary Structure
--------------------------------

This section describes the input paramaters used by the data modules.

.. note::

   This assumes the schema template provided in the `keg-recipes repository
   <https://github.com/SUSE-Enceladus/keg-recipes>`. Custom templates may
   require different input data.

.. code:: yaml

  profile:
    bootloader:
      kiwi_bootloader_param: string
      ...
    parameters:
      kiwi_peferences_type_param: string
      ...
      kernelcmdline:
        kernel_param: value
        kernel_multi_param: [value, value]
        ...
    size: integer
  packages:
    packages_type:
      namespace:
        - string
        - name: string
          arch: string
  config:
    files:
      namespace:
        - path: /path/to/file
          append: bool
          content: string
        ...
    scripts:
      namespace:
        - string
        ....
    sysconfig:
      namespace:
        - file: /etc/sysconfig/file
          name: VARIABLE_NAME
          value: VARIABLE_VALUE
        ...
    services:
      namespace:
        - string
        - name: string
          enable: bool
        ...
  setup:
    (same as config)
  overlayfiles:
    namespace:
      include:
        - string
        ...
    namespace_named_archive:
      archivename: string
      include:
        - string
        ...

.. note::

  For multi-build image definitions, any module that defines `profile`
  parameters must be included in the profile specific section of the image
  definition. Inclusion in the `common` profile only works for single-build
  image definitions.

Namespace may be any name. Namespaces exist to allow for dictionaries to be
merged without overwriting keys from inherited dictionaries, except where this
is wanted. Using the same namespace in a more specific dictionary (i.e. a lower
level directory) can be used to change or even remove that namespace (for the
latter set it to `Null`).

`kiwi_bootloader_param` refers to any bootloader type parameter supported by
`kiwi <https://documentation.suse.com/kiwi/9/html/kiwi/building-types.html#disk-bootloader>`__.

`kiwi_peferences_type_param` refers to any preferences type parameter supported
by `kiwi` (see `\<preferences\>\<type\> in kiwi documentation
<https://documentation.suse.com/kiwi/9/html/kiwi/image-description.html#sec-preferences>`__).

`kernelcmdline` is not a string that is directy copied into the appropriate
`kiwi` parameter but a dictionary that defines kernel parameters individually,
with each key representing a kernel parameter. This allows to inherit parts of
the kernel command line from other modules. There are two notiations for
parameters.  `kernel_param: value` will be translated into a single
`kernel_param=value`, and `kernel_multi_param: [value, value, ...]` will add
`kernel_multi_param` multiple times for each value from the given list.

`packages_type` can be `bootstrap` or `image` (see `kiwi documentation
<https://documentation.suse.com/kiwi/9/html/kiwi/image-description.html#sec-packages>`__).
The items in the package list have two possible notations. Either just a plain
string, which is considered to be the package name, or a dictionary with keys
`name` (the package name) and `arch` (the build architecture for which the
package should be included).

List items in `config` `script` refer to files in :file:`data/scripts` (with
:file:`.sh` appended by `keg`) and the content of those will be added to the
:file:`config.sh` script.

List items in `config` `services` refer to system service that should be
enabled or disabled in the image. Analogue to packages, there are two supported
version, a short one containing only the service name, or a long one that
allows to specify whether the service should be enabled or disabled).

`setup` has the same structure as `config` but the data will be used to
generated :file:`images.sh` instead of :file:`config.sh`.

List items in `overlayfiles` refer to directories under
:file:`data/overlafiles`. Files from those directories will be copied into
an overlay archive to be included in the image, either a generic or a profile
specific one (depending on where the data module was included), or a named one
in case `archivename` tag is used.

