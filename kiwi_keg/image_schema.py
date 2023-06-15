# Copyright (c) 2022 SUSE Software Solutions Germany GmbH. All rights reserved.
#
# This file is part of keg.
#
# keg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# keg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with keg. If not, see <http://www.gnu.org/licenses/>
#
from schema import (
    Schema, And, Or, Optional
)
from kiwi_keg.annotated_mapping import AnnotatedMapping


class NamespaceSchema(Schema):
    def __init__(self, schema, **kwargs):
        # Generally ignore extra keys; this schema is a sub-set of the full
        # kiwi schema.
        kwargs['ignore_extra_keys'] = True
        super().__init__(schema, **kwargs)

    def validate(self, data):
        if isinstance(data, dict) and '_namespace' in [x[:10] for x in data.keys()]:
            namespaces = [x for x in data.keys() if x.startswith('_namespace')]
            # We create a copy of the input data, remove all namespace keys,
            # then copy each namespace into the copied dict and validate.
            # This way namespaces seem invisible and don't have to be accounted
            # for in the schema, but all namespaced data is validated against
            # the schema.
            for ns in namespaces:
                tmp = data.copy()
                for del_ns in namespaces:
                    del tmp[del_ns]
                tmp.update(data[ns])
                val = super().validate(tmp)
        else:
            val = super().validate(data)
        return val


class ImageSchema():
    def __init__(self):
        self._schema = Schema(
            {
                Optional('schema'): And(str),
                Optional('include-paths'): [And(str)],
                'image': NamespaceSchema({
                    '_attributes': {
                        'schemaversion': And(str),
                        'name': And(str),
                        Optional('displayname'): And(str),
                    },
                    'description': {
                        '_attributes': {
                            'type': And(str),
                        },
                        'author': And(str),
                        'contact': And(str),
                        'specification': And(str)
                    },
                    Optional('profiles'): {
                        Optional('profile'): [{
                            '_attributes': {
                                'name': And(str),
                                'description': And(str)
                            }
                        }],
                    },
                    'preferences': Or(
                        [
                            {
                                'version': And(str),
                            },
                            Optional(
                                {
                                    '_attributes': {
                                        'profiles': [str],
                                        Optional('arch'): And(str)
                                    },
                                    'type': {
                                        '_attributes': {
                                            'image': And(str)
                                        }
                                    }
                                }, ignore_extra_keys=True
                            )
                        ],
                        {
                            'version': And(str),
                        },
                        ignore_extra_keys=True
                    ),
                    'repository': [
                        {
                            '_attributes': {
                                'type': And(str)
                            },
                            'source': {
                                '_attributes': {
                                    'path': And(str)
                                }
                            }
                        }
                    ],
                    'packages': [
                        {
                            '_attributes': {
                                'type': And(str),
                                Optional('profiles'): [str]
                            },
                            Optional('_map_attribute'): And(str),
                            Optional('archive'): [
                                {
                                    '_attributes': {
                                        'name': And(str),
                                    }
                                }
                            ],
                            'package': [
                                Or(
                                    str,
                                    {
                                        '_attributes': {
                                            'name': And(str),
                                            Optional('arch'): Or(str, [str])
                                        }
                                    },
                                    ignore_extra_keys=True
                                )
                            ]
                        }
                    ],
                    Optional('drivers'): [
                        {
                            Optional('_map_attribute'): And(str),
                            'file': [
                                Or(
                                    str,
                                    {
                                        '_attributes': {
                                            'name': And(str),
                                            Optional('arch'): Or(str, [str])
                                        }
                                    },
                                    ignore_extra_keys=True
                                )
                            ]
                        }
                    ],
                }),
                Optional('config'): [
                    Or(
                        {
                            'files': {
                                str: [{
                                    Optional('append'): And(bool),
                                    'content': And(str),
                                    'path': And(str)
                                }]
                            }
                        },
                        {
                            'scripts': {
                                str: [str]
                            },
                        },
                        {
                            'services': {
                                str: [Or(str, {'name': And(str), Optional('enable'): And(bool)}, ignore_extra_keys=True)]
                            },
                        },
                        {
                            'sysconfig': {
                                str: [{'file': And(str), 'name': And(str), 'value': And(str)}]
                            }
                        },
                        ignore_extra_keys=True
                    )
                ],
                Optional('setup'): [
                    Or(
                        {
                            'files': {
                                str: [{
                                    Optional('append'): And(bool),
                                    'content': And(str),
                                    'path': And(str)
                                }]
                            }
                        },
                        {
                            'scripts': {
                                str: [str]
                            },
                        },
                        {
                            'services': {
                                str: [Or(str, {'name': And(str), Optional('enable'): And(bool)}, ignore_extra_keys=True)]
                            },
                        },
                        {
                            'sysconfig': {
                                str: [{'file': And(str), 'name': And(str), 'value': And(str)}]
                            }
                        },
                        ignore_extra_keys=True
                    )
                ],
                Optional('archive'): [
                    {
                        'name': And(str),
                        str: {
                            '_include_overlays': [str]
                        }
                    }
                ],
                Optional('xmlfiles'): [
                    {
                        'name': And(str),
                        'content': And(dict)
                    }
                ]
            },
            ignore_extra_keys=True
        )

    def validate(self, data):
        if isinstance(data, AnnotatedMapping):
            self._schema.validate(data.to_dict())
        else:
            self._schema.validate(data)
