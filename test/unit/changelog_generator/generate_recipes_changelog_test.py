import os
import sys
from pytest import raises
from tempfile import TemporaryDirectory, NamedTemporaryFile
from kiwi_keg.changelog_generator.generate_recipes_changelog import (
    main,
    get_commits,
    get_commit_message
)

expected_output_text = """\
- Generate config.sh and images.sh directly
- Generate overlay archive tags for schema
- Generate overlay tarball
- add unit test coverage for delete-key support
- Update overlay structure
- Add support for images.sh script
- Add template functions tests
"""

expected_output_yaml = """\
- change: Generate config.sh and images.sh directly
  details: |-
    This moves generating the config scripts into keg rather than relying on
    templates in keg-recipes. Use of templates is still supported to generate
    script headers which can be used to provide additional information available
    from the data dictionary.
- change: Generate overlay archive tags for schema
  details: |-
    Process overlay data when the image defintion is populated, and add archive
    tags to the profile sections for use in schema templates.
    Also add collected archive information to data dictonary root, for easier
    archive generation later.
    Simplify archive generation, produce tarball directly without intermediate
    copy, and set file ownership to 'root'.
    Change mockup recipes data to be more in line with real data layout.
- change: Generate overlay tarball
  details: |-
    - Use the new defined overlay structure
- change: add unit test coverage for delete-key support
  details: |-
    Adds a key to a (not actually produced) Leap <= 15.1 image description and
    removes it for the Leap 15.2 one that is used in the unit test. This will cover
    the corresponding code path.

    This also required a slight rearrangment of the mockup image defintion, as it
    wasn't quite using the appropriate keg data layout.
- change: Update overlay structure
  details: |-
    - Parse overlay yaml allowing duplicate keys
    - Check overlaynames are present
    - Create different overlay tarballs
    - Update config.kiwi with the proper archive elements
- change: Add support for images.sh script
  details: |-
    Unfortunately adding support for another script hook was not
    possible without changing the layout of the image definition
    data for scripts. The basic structure for the scripts config.sh
    and images.sh is now as follows:

    ```yaml
    config:
      # config.sh setup
      config_script:
        NAMESPACE:
          - SCRIPTLET_NAME
        files:
          NAMESPACE:
            - PATH_DEFINITION
        services:
          NAMESPACE:
            - SERVICE_DEFINITION
        sysconfig:
          NAMESPACE:
            - FILE_DEFINITION

      # images.sh setup
      image_script:
        SAME_STRUCTURE_AS_FOR_CONFIG_SCRIPT
    ```

    On merge of this commit the data structure in the keg-recipes
    repository must be adapted. This Fixes #35
- change: Add template functions tests
  details: |-
    - Test template functions
    - Add type hints
    - Rename parse_yaml_tree method to get_yaml_tree

    This Fixes #12
"""


class TestGenerateRecipesChangelog:
    def setup(self):
        sys.argv = [
            sys.argv[0],
            '-r', '58f498777e8a61facbf3b15ec9104699905a0369..29d440ca60929d166924fe534c69be5b247a3eb3',
            '-f', 'text',
            '-C', '.',
            '../data/keg_output_source_info/log_sources'
        ]

    def test_generate_recipes_changelog(self, capsys):
        main()
        cap = capsys.readouterr()
        assert cap.out == expected_output_text

    def test_generate_recipes_changelog_yaml(self):
        sys.argv[4] = 'yaml'
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert open(tmpfile, 'r').read() == expected_output_yaml

    def test_generate_recipes_changelog_yaml_title(self, capsys):
        sys.argv[4] = 'yaml'
        sys.argv.append('-t')
        sys.argv.append('title')
        main()
        cap = capsys.readouterr()
        assert cap.out == 'title:\n' + expected_output_yaml

    def test_yaml_short_message(self, capsys):
        with NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b'README.rst\n')
            tmpfile.flush()
            sys.argv = [
                sys.argv[0],
                '-r', '2c0af00a880e8f5cd0d9631e740efa551d2cf370..d220475df1ace395ce8197ff4ec5947c114e19ff',
                '-f', 'yaml',
                '-C', '../..',
                tmpfile.name
            ]
            main()
            cap = capsys.readouterr()
        assert cap.out == '- change: Consolidate README into ReST\n'

    def test_get_commits_error(self):
        gitcmd = ['git', 'log', 'no_such_path']
        with raises(Exception) as err:
            get_commits(gitcmd)
        assert 'unknown revision or path not in the working tree' in str(err.value)

    def test_get_commit_message_error(self):
        with raises(Exception) as err:
            get_commit_message('no_such_hash', '%s')
        assert 'unknown revision or path not in the working tree' in str(err.value)

    def test_unsupported_format_error(self):
        sys.argv[4] = 'foo'
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'Unsupported output format "foo".'
