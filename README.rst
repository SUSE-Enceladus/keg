KEG - Image Compositon Tool
===========================

.. |GitHub CI Action| image:: https://github.com/SUSE-Enceladus/keg/workflows/CILint/badge.svg?branch=main
   :target: https://github.com/SUSE-Enceladus/keg/actions

|GitHub CI Action|

keg is a command line tool that creates a
`kiwi <https://github.com/OSInside/kiwi>`_ image description based on
description snippets in a given GIT repository.

Contributing
------------

keg is written in Python, it uses `tox <https://tox.readthedocs.io/en/latest/>`_
to setup a development environment for the desired Python version. Make
sure the Python development headers are installed (e.g. `python36-devel`).
KIWI uses `jing` for detailed error reporting in case schema validation fails.
This cannot be installed by pip, so you may want also make sure this is
installed on your system.

Currently, there are 5 targets for tox:

- **check**: for code quality and integrity
- **devel**: for development
- **doc**: for building man pages
- **unit_py3_8**: to run unit tests with Python version set to *3.8*
- **unit_py3_6**: to run unit tests with Python version set to *3.6*

The following procedure describes how to create the development environment:

1. Let tox create the virtual environment(s):

   .. code:: bash

       $ tox -e devel

2. Activate the virtual environment
    
   .. code:: bash

       $ source .tox/3/bin/activate

3. Install requirements inside the virtual environment:

   .. code:: bash

       $ pip install -U pip setuptools
       $ pip install -r .virtualenv.dev-requirements.txt

4. Let setuptools create/update your entrypoints

   .. code:: bash

       $ ./setup.py develop

Once the development environment is activated and initialized with
the project required Python modules, you are ready to work.

In order to leave the development mode just call:

.. code:: bash

   $ deactivate

To resume your work, change into your local Git repository and
run `source .tox/3/bin/activate` again. Skip step 3 and 4 as
the requirements are already installed.
