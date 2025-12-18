from pytest import raises
from unittest.mock import patch, Mock, call, mock_open

from kiwi_keg.kiwi_description import KiwiDescription

from kiwi_keg.exceptions import (
    KegDescriptionNotFound,
    KegKiwiValidationError,
    KegKiwiDescriptionError
)


@patch('os.path.isfile', return_value=False)
def test_kiwi_description_init_raises(mock_isfile):
    with raises(KegDescriptionNotFound):
        KiwiDescription('does-not-exist')


@patch('kiwi_keg.kiwi_description.XMLDescription')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_validate_description(mock_isfile, mock_xml_description):
    kiwi = KiwiDescription('config.xml')
    mock_description_obj = Mock()
    mock_xml_description.return_value = mock_description_obj
    kiwi.validate_description()
    mock_description_obj.load.assert_called_once()


@patch('kiwi.xml_description.XMLDescription')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_validate_description_invalid(mock_isfile, mock_xml_description):
    mock_xml_description.side_effect = Exception('validation error')
    kiwi_invalid = KiwiDescription('config.xml')
    with raises(KegKiwiValidationError):
        kiwi_invalid.validate_description()


@patch('kiwi_keg.kiwi_description.KiwiDescription._create_description')
@patch('kiwi_keg.kiwi_description.KiwiDescription._read_XML_comments')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_create_XML_description(mock_isfile, mock_read_xml_comments, mock_create_description):
    mock_read_xml_comments.return_value = '<!-- comment -->'
    kiwi = KiwiDescription('config.xml')
    with patch('builtins.open') as mock_file:
        kiwi.create_XML_description('output.xml')
        mock_read_xml_comments.assert_called_once()
        mock_create_description.assert_called_once_with('output.xml', 'xml')
        mock_file.assert_has_calls([
            call('output.xml', 'w'),
            call().__enter__(),
            call().__enter__().write('<!-- comment -->'),
        ])


@patch('kiwi_keg.kiwi_description.KiwiDescription._create_description')
@patch('kiwi_keg.kiwi_description.KiwiDescription._read_YAML_comments')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_create_YAML_description(mock_isfile, mock_read_yaml_comments, mock_create_description):
    kiwi = KiwiDescription('config.xml')
    kiwi.create_YAML_description('output.yaml')
    mock_read_yaml_comments.assert_called_once()
    mock_create_description.assert_called_once_with('output.yaml', 'yaml')


@patch('kiwi_keg.kiwi_description.KiwiDescription.validate_description')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_create_description_failed(mock_isfile, mock_validate_description):
    kiwi = KiwiDescription('config.xml')
    mock_description = Mock()
    mock_validate_description.return_value = mock_description
    mock_description.markup.get_xml_description.side_effect = Exception
    with raises(KegKiwiDescriptionError):
        kiwi._create_description('output.xml', 'xml')


@patch('kiwi_keg.kiwi_description.KiwiDescription.validate_description')
@patch('shutil.copy')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_create_description_xml(mock_isfile, mock_copy, mock_validate_description):
    kiwi = KiwiDescription('config.xml')
    mock_description = Mock()
    mock_validate_description.return_value = mock_description
    mock_description.markup.get_xml_description.return_value = 'doc'
    kiwi._create_description('output.xml', 'xml')
    mock_description.markup.get_xml_description.assert_called_once()
    mock_copy.assert_called_once_with('doc', 'output.xml')


@patch('kiwi_keg.kiwi_description.KiwiDescription.validate_description')
@patch('shutil.copy')
@patch('os.path.isfile', return_value=True)
def test_kiwi_description_create_description_yaml(mock_isfile, mock_copy, mock_validate_description):
    kiwi = KiwiDescription('config.xml')
    mock_description = Mock()
    mock_validate_description.return_value = mock_description
    mock_description.markup.get_yaml_description.return_value = 'doc'
    kiwi._create_description('output.yaml', 'yaml')
    mock_description.markup.get_yaml_description.assert_called_once()
    mock_copy.assert_called_once_with('doc', 'output.yaml')


@patch('os.path.isfile', return_value=True)
def test_kiwi_description_read_yaml_comments(mock_isfile):
    kiwi = KiwiDescription('config.xml')
    kiwi._read_YAML_comments()


XML_comments = '''
<?xml?>
<!-- single line comment -->
<not a comment/>
<!-- multi
line
comment -->
'''


@patch('os.path.isfile', return_value=True)
def test_kiwi_description_read_xml_comments(mock_isfile):
    kiwi = KiwiDescription('config.xml')
    mo = mock_open(read_data=XML_comments)
    with patch('builtins.open', mo):
        comments = kiwi._read_XML_comments()
        assert '<!-- single line comment -->\n' in comments
        assert '<!-- multi\n' in comments

    mo.assert_called_once_with('config.xml', 'r')
