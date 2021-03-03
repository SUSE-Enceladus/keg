.. _overview:

Overview
========

.. note:: **Abstract**

   This document provides a conceptual overview about the steps of creating
   an image description with `keg` which can be used to build an appliance
   with the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder.

Conceptual Overview
-------------------

Keg is a tool which helps to create and manage image descriptions suitable
for the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder. 
While `keg` can be used to manage a single image definition the tool provides
no considerable advantage in such a use case. The primary use case for keg
are situations where many image descriptions must be managed and the
image descriptions have considerable over lap with respect to content
and setup.

The key component for `keg` is a data structure called `image definition tree`.
This data structure is expected to contain all information necessary to
create KIWI image descriptions. `keg` is implemented such that data inheritance 
is possible to reduce data duplication in the `image definition tree`.

The `image definition tree` consists of three major components:

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
part when using Keg. Example definitions for the `image definition tree`
can be found here:
`Public Cloud Image Definition Tree <https://github.com/SUSE-Enceladus/keg-recipes>`__

Working With Keg
----------------

Using `keg` is a two step process:

1. Fetch or create an `image definition tree`

2. Call the `keg` commandline utility to create a KIWI image description

For the above to work, Keg needs to be installed as described in
:ref:`installation`. In addition install KIWI:
https://osinside.github.io/kiwi/installation.html

If all software components are installed, `keg` can be utilized like
the following example shows:

.. code:: shell-session

    $ git clone https://github.com/SUSE-Enceladus/keg-recipes.git

    $ keg --recipes-root keg-recipes --dest-dir leap_description \
          leap/jeos/15.2

After the `keg` command completes the destination directory specified
with `--dest-dir` contains and image description that can be processed
with kiwi to build an image. For more details about kiwi image descriptions
see: https://osinside.github.io/kiwi/image_description.html

With kiwi installed you can build the image with the `keg` created image
description as follows:

.. code:: shell-session

    $ sudo kiwi-ng system build --description leap_description \
          --target-dir leap_image
