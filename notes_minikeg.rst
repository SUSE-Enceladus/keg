Keg redesign codename "minikeg"
===============================

Purpose
-------

Make keg flexible enough to produce any possible kiwi image description
(theoretically) and get rid of the jinja2 template, which mutated over
time into an awkward XML generator with limited functionality.

Why codename minikeg
--------------------

Because the new design minimizes "special sauce". Keg won't construct
the image description's preferences, profiles, and packages section anymore.
These structures are now part of the user defined image definition.

General design notes
--------------------

The image definition is now a representation of the kiwi description, so
key names and structures have been adjusted to be in line with the kiwi
schema. The previous profile driven approach had functionality to parse
the profile data and produce XML elements accordingly, more specifically
the preferences, profiles, and packages section, plus code that injects
'archive' tags into the packages section. With minikeg, the user defines
the full data definition. To support existing modularity, there is an
include directive with merges data blocks into the main dictionary. The
image definition is translated by keg into a kiwi file directly with its
new built-in XML generator. Template support has not been removed so this
could still be used, but will require adapted templates.

Changes in image definition
---------------------------

As mentioned, the image dictionary is now a direct representation of the kiwi
XML description. Instead of special knowledge in keg or more precisely the
recipes template about what key is mapped to an XML attribute or to a child
node, it's now up to the user to define this. To allow the user to do this,
special keys have been introduced to keg recipes. Those keys start with an
underscore to distinguish them from regular data tags. The following special
keys exist:

.. code::
_attributes: XML attributes
_comment: produces an XML comment in the output before the element defined by
          the key the _comment key is attached to
_include: merge in dictionary from given path
_namespace*: used to namespace blocks (not related to XML namespaces);
             namespace keys do not produce an XML element itself,
             but a comment will be produced
_map_attribute: defines an attribute strings get mapped to, convenience
                feature
_text: defines basic text content for an element

Merging of dictionaries hasn't fundamentally changed. YAML files are read
from top dir level to lower levels, so lower level keys replace the
same keys from higher levels. The `_include` directive reads YAML files
from the given path (plus include-paths extensions), and creates the
dict to merge into the main dict. Keg looks for a key in the include
dict that matches to the key the `_include` statement is under.
So for instance, let's assume  we have the following in the image definition:

.. code:: yaml
  image:
    preferences:
      - _include: base/common
    packages:
      - _attributes:
          type: image
        _include:
          - base/common

The dictionary created from base/common is initially the same for both
includes, but only preferences will be merged into preferences, and packages
into packages. That means you can have all your configuration bits that belong
together logically in one place (preferences, packages, etc) and simply include
it at different places in the image dictionary.

config.sh and image.sh
----------------------

For generating config.sh and images.sh, new top level keys was added to the
main dictionary, namely `config` and `setup`. The structure is pretty simple:

.. code:: yaml
  config:
    - profiles: [Some-Profile, Another-Profile]
      _include:
        - some/stuff
        - other/stuff

The `_include` mechanism works the same as above and is used to pull modules
in. The structure in the data path wrt configuration has not changed, so
existing config.sh data can be uses as-is.

Overlay archives
----------------

Overlay archive configuration is now split into two bits in the image
definition. Archives need to be declared in the image definition under the
`packages` section (just as anything else that kiwi expects). Their content is
defined under a new top-level key, and follows the same principle as the other
definition bits:

.. code:: yaml
  archive:
    - name: root.tar.gz
      _include:
        - products/sles
    - name: azure.tar.gz
      _include:
        - csp/azure

Every `archive` item results in keg producing an archive with the given
name. They can be referenced in the image definition accordingly to assign them
to one or more profiles. :file:`root.tar.gz` is included automatically by kiwi.
Analog to `config`, the structure in the data path has not really changed,
although the `include` keyword was changed to `overlay` to make it more
obvious that it's not the same as `_include`.

Changes in data source format
-----------------------------

Since preferences are not processed by keg anymore, the data structure of
the preferences configuration need to be aligned to the kiwi schema, which
means the existing configuration under `profile` needs to be mapped to
`preferences`. For example,

.. code:: yaml
  profile:
    parameters:
      image: vmx
      ...

needs to be changed to

.. code:: yaml
  preferences:
    type:
      _attributes:
        image: vmx
        ...

Packages sections will need existing namespaces change to the new namespace
tags and need to get a `package` key:

.. code:: yaml
  packages:
    _map_attribute: name
    _namespace_common:
      package:
        - some_package
        - another_package
        ...

The `_map_attribute` tag instructs the XML generator to map the list of strings
(package names in this case) to a list of dictionaries that looks like this:

.. code:: yaml
  package:
    - _attributes:
        name: some_package
    - _attributes:
        name: another_package

This can be used to keep package lists more compact.

Build architecture and filtering
--------------------------------

Keg now has a command line argument to specify one or more architectures for
which the to-be-generated image description should be enabled. When used,
this will add the appropriate `OBS-ExclusiveArch` comment to the image
description, and will also set up a filter in the XML generator. The XML
generator has a generic filter mechanism for attributes, which is used in
this case to skip any section that is defined only for architectures that
are not enabled.
