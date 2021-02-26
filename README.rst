KEG - Image Compositon Tool
===========================

.. |Build Status| image:: https://travis-ci.com/SUSE-Enceladus/keg.svg?branch=main
   :target: https://travis-ci.com/SUSE-Enceladus/keg

|Build Status|

keg is a command line tool that creates a
[kiwi](https://github.com/OSInside/kiwi) image description based on
description snippets in a given GIT repository.


## Contents

  * [Contributing](#contributing)

## Contributing

keg is written in Python, it uses [tox](https://tox.readthedocs.io/en/latest/) to setup a development environment
for the desired Python version. Make sure the Python development headers
are installed (e.g. `python36-devel`)

The following procedure describes how to create such an environment:

1.  Let tox create the virtual environment(s):

    ```
    $ tox
    ```

2.  Activate the virtual environment

    ```
    $ source .tox/3/bin/activate
    ```

3.  Install requirements inside the virtual environment:

    ```
    $ pip install -U pip setuptools
    $ pip install -r .virtualenv.dev-requirements.txt
    ```

4.  Let setuptools create/update your entrypoints

    ```
    $ ./setup.py develop
    ```

Once the development environment is activated and initialized with
the project required Python modules, you are ready to work.

In order to leave the development mode just call:

```
$ deactivate
```

To resume your work, change into your local Git repository and
run `source .tox/3/bin/activate` again. Skip step 3 and 4 as
the requirements are already installed.
