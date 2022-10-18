.. _overview:

Overview
========

.. note:: **Abstract**

   This document provides a conceptual overview about the steps of creating
   an image description with `keg` which can be used to build an appliance
   with the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder.

.. note::

   Copyright © 2022 SUSE LLC and contributors. All rights reserved.

   Except where otherwise noted, this document is licensed under Creative
   Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0):
   https://creativecommons.org/licenses/by-sa/4.0/legalcode.

   For SUSE trademarks, see http://www.suse.com/company/legal/. All third-party
   trademarks are the property of their respective owners. Trademark symbols (®, ™
   etc.) denote trademarks of SUSE and its affiliates. Asterisks (*) denote
   third-party trademarks.

   All information found in this book has been compiled with utmost attention
   to detail. However, this does not guarantee complete accuracy. Neither SUSE
   LLC, its affiliates, the authors nor the translators shall be held liable for
   possible errors or the consequences thereof.

Conceptual overview
-------------------

Keg is a tool which helps to create and manage image descriptions for use with
the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder. A `KIWI`
image description consists of a single XML document that specifies type,
configuration, and content of the image to build. Optionally there can be
configuration scripts and overlay archives added to an image description,
which allow for further configuration and additional content.

Since `KIWI` image descriptions are monolithic, maintaining a number of image
descriptions that have considerable overlap with respect to content and setup
can be cumbersome and error-prone. `Keg` attempts to alleviate that by
allowing image descriptions to be broken into modules. Those modules can be
composed in different ways in so called image definitions, and modules can
inherit from parent modules which allows for fine-tuning for specific image
setups. Configuration scripts and overlay archives can also be generated in a
modular fashion.

The collection of source data required for `keg` to produce image descriptions
is called `recipes`. `Keg recipes` are typically kept in a `git` repository,
and `keg` has support for producing change logs from `git` commit history, but
this is not a requirement. A `recipes` repository provides `keg` with the
information how an image description is to be composed as well as the content
of the components.

The basic principle of operation is that when `keg` is executed, it is pointed
to a directory within the `recipes` repository and it reads any YAML files in
that directory and any parent directories and merges their contents into a
dictionary. How the image definition data is structured and composed is not
relevant, as long as the resulting dictionary represents a valid image
definition. This allows for a lot of flexibility in the layout of a `recipes`
repository. The `SUSE Public Cloud Keg Recipes repository
<https://github.com/SUSE-Enceladus/keg-recipes>`__ provides an example of a
highly modular one with strong use of inheritance.

For more details on what constitutes a `recipes` repository, see section
:ref:`recipes_basics` (ff).

Working with keg
----------------

To create an image description, `keg` needs to be installed, as well
as `KIWI`, as the latter is used by `keg` to validate the final image
description. See :ref:`installation` for information about how to install
`keg`, and `KIWI Installation
<https://osinside.github.io/kiwi/installation.html>`_ about how to install
`KIWI`.

Additionally, a `recipes` repository is required. The following example uses
the aforementioned SUSE Public Cloud keg recipes:

.. code:: shell-session

    $ git clone https://github.com/SUSE-Enceladus/keg-recipes.git

    $ mkdir sles15-sp4-byos

    $ keg --recipes-root keg-recipes --dest-dir sles15-sp4-byos \
          cross-cloud/sles/byos/15-sp4

After the `keg` command completes the destination directory specified with
`--dest-dir` contains a description for a SUSE Linux Enterprise Server 15 SP4
image for use in the Public Clouds. It can be processed with KIWI to build an
image. For more details about KIWI image descriptions, see
https://osinside.github.io/kiwi/image_description.html.

`Recipes` used to generate an image description can be spread over multiple
repositories. For that purpose, the `--recipes-root` command line argument may
be given multiple times, with each one specifying a different `recipes`
repository. Repositories will be searched in the order they are specified, and
for any dictionary key, config scriptlet, or overlay archive module that
exists in multiple repositories, the one that is read last will be used.

Using multiple repositories for `recipes` can be useful in some
situations. For example, if some parts of `recipes` data are public and some
private, they can be kept in different repositories. It could also be used to
base `recipes` on an upstream repository and only maintain additional image
definitions or modifications in a separate repository.

`Keg` also provides support for producing image descriptions for use with the
`Open Build Service
<https://openbuildservice.org/help/manuals/obs-user-guide/>`_. It can generate
`_multibuild` files that are required by `OBS` for image descriptions with
multiple profiles, and it comes with an `OBS Source Service` plug-in for
automating generating image descriptions. See :ref:`keg_obs_source_service`
for details.
