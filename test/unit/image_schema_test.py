from kiwi_keg.image_schema import ImageSchema
from kiwi_keg.annotated_mapping import AnnotatedMapping

test_image_def = {
    'include-paths': ['some-include-path'],
    'image': {
        '_attributes': {
            'schemaversion': '7.5',
            'name': 'image_name',
            'displayname': 'display_name'
        },
        'description': {
            '_attributes': {
                'type': 'system'
            },
            'author': 'author',
            'contact': 'author@place',
            'specification': 'Some image spec'
        },
        'profiles': {
            'profile': [
                {
                    '_attributes': {
                        'name': 'base_profile',
                        'description': 'base profile'
                    }
                },
                {
                    '_attributes': {
                        'name': 'profile_one',
                        'description': 'profile one'
                    },
                    'requires': [
                        {
                            '_attributes': {
                                'profile': 'base_profile'
                            }
                        }
                    ]
                }
            ]
        },
        'preferences': [
            {
                'version': '1.0.0'
            },
            {
                '_attributes': {
                    'profiles': ['profile_one'],
                    'arch': 'profile_arch'
                },
                'type': {
                    '_attributes': {
                        'image': 'oem'
                    }
                }
            }
        ],
        'repository': [
            {
                '_attributes': {
                    'type': 'repo_type'
                },
                'source': {
                    '_attributes': {
                        'path': 'repo_path'
                    }
                }
            }
        ],
        'packages': [
            {
                '_attributes': {
                    'type': 'image',
                    'profiles': ['profile_one']
                },
                '_map_attribute': 'name',
                'archive': [
                    {
                        '_attributes': {
                            'name': 'archive_name'
                        }
                    }
                ],
                'package': [
                    'package_mapped_attributes',
                    {
                        '_attributes': {
                            'name': 'package_explicit_attributes',
                            'arch': 'package_arch'
                        }
                    }
                ],
                '_namespace_packages': {
                    'package': [
                        'namespaced_package'
                    ]
                }
            }
        ],
        'drivers': [
            {
                '_map_attribute': 'name',
                'file': [
                    'mapped_file',
                    {
                        '_attributes': {
                            'name': 'explicit_file',
                            'arch': 'file_arch'
                        }
                    }
                ]
            }
        ],
        'config': [
            {
                'files': {
                    'section_name': [
                        {
                            'append': True,
                            'content': 'file_content',
                            'path': 'file_path'
                        }
                    ]
                }
            },
            {
                'scripts': {
                    'section_name': [
                        'script_name'
                    ]
                }
            },
            {
                'services': {
                    'section_name': [
                        'service_short_format',
                        {
                            'name': 'service_long_format',
                            'enable': False
                        }
                    ]
                }
            },
            {
                'sysconfig': {
                    'section_name': [
                        {
                            'file': 'sysconfig_file',
                            'name': 'sysconfig_variable',
                            'value': 'sysconfig_value'
                        }
                    ]
                }
            }
        ],
        'setup': [
            {
                'files': {
                    'section_name': [
                        {
                            'append': True,
                            'content': 'file_content',
                            'path': 'file_path'
                        }
                    ]
                }
            },
            {
                'scripts': {
                    'section_name': [
                        'script_name'
                    ]
                }
            },
            {
                'services': {
                    'section_name': [
                        'service_short_format',
                        {
                            'name': 'service_long_format',
                            'enable': False
                        }
                    ]
                }
            },
            {
                'sysconfig': {
                    'section_name': [
                        {
                            'file': 'sysconfig_file',
                            'name': 'sysconfig_variable',
                            'value': 'sysconfig_value'
                        }
                    ]
                }
            }
        ],
    },
    'archive': [
        {
            'name': 'archive_name',
            'namespace': {
                '_include_overlays': ['overlay']
            }
        }
    ],
    'xmlfiles': [
        {
            'name': 'xml_file_name',
            'content': {
                'xml': 'data'
            }
        }
    ]
}


def test_image_schema_dict():
    img_schema = ImageSchema()
    img_schema.validate(test_image_def)


def test_image_schema_annotated_mapping():
    img_schema = ImageSchema()
    img_schema.validate(AnnotatedMapping(test_image_def))
