.. _overview:

Overview
========

.. note:: **Abstract**

   This document provides a conceptual overview about the steps of creating
   an image description with keg which can be used to build an appliance
   with the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder.

Conceptual Overview
-------------------

Keg is a tool which helps to create and manage image descriptions suitable
for the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder. Its
main use case is to keep control over a larger amount of image descriptions
and prevent duplication of description data.

The key component for Keg is a data structure called `image definition tree`.
This data structure contains all information to create KIWI image
descriptions and provides data in a way that no or as little as possible
duplication exists. The `image definition tree` consists out of three
major components:

Data Building Blocks: :file:`data`
  Independent collection of components used in KIWI image
  descriptions. This includes for example information about
  packages, repositories or custom script code and more.
  A building block should be created to represent a certain
  functionality or to provide a capability for a certain
  target distribution such that it can be used in a variety
  of different image descriptions. 

Image Definitions: :file:`images`
  Formal instructions which building blocks should be used for
  the specified image

Schema Templates: :file:`schemas`
  Templates to implement Syntax and Semantic of image description
  files as required by KIWI

The setup of the `image definition tree` is the most time consuming
part when using Keg. Because of this reason it's part of the Keg
project to provide one implementation of such a tree as a service to
our users. The provided information will be done with the scope set
on **Public Clouds**. As we from the public cloud development team
use Keg to manage our own image descriptions it's natural that the
provided data in the open source project is aligned to cloud
environments. However, this is not a limitation and we welcome any
contributions independent of the target they serve. Please find
our `image definition tree` here:
`Public Cloud Image Definition Tree <https://github.com/SUSE-Enceladus/keg-recipes>`__

Working With Keg
----------------

Using Keg is done in three steps:

1. Fetch or create an `image definition tree`

2. Call the `keg` commandline utility to create a KIWI image description

3. Call `kiwi-ng` and create an appliance from the description

For the above to work, Keg needs to be installed as described in
:ref:`installation`. In addition install KIWI as described here:
https://osinside.github.io/kiwi/installation.html

If all software components are installed, Keg can be utilized like
the following example shows:

.. code:: shell-session

    $ git clone https://github.com/SUSE-Enceladus/keg-recipes.git

    $ keg --recipes-root keg-recipes --dest-dir leap_description \
          leap/jeos/15.2

    $ sudo kiwi-ng system build --description leap_description \
          --target-dir leap_image
