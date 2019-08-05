
class SwaggerDoc():
    def __init__(self): pass
    
    def getDocs(self):

        return {
            'swagger': '2.0',
            'info': {
                'title': 'CCE Search',
                'description': 'API for searching Copyright Registrations and Renewals',
                'contact': {
                'responsibleOrganization': 'NYPL',
                'responsibleDeveloper': 'Michael Benowitz',
                'email': 'michaelbenowitz@nypl.org',
                'url': 'www.nypl.org',
                },
                'version': 'v0.1'
            },
            'basePath': '/',  # base bash for blueprint registration
            'schemes': [
                'http',
                'https'
            ],
            'paths': {
                '/search/fulltext': {
                    'get': {
                        'tags': ['Search'],
                        'summary': 'Returns a set of registration and renewal objects',
                        'description': 'Accepts a search_query string with full boolean logic to fuzzy search across both registration and renewal records',
                        'parameters': [
                            {
                                'name': 'query',
                                'in': 'query',
                                'type': 'string',
                                'required': True,
                                'default': '*'
                            },{
                                'name': 'source',
                                'in': 'query',
                                'type': 'boolean',
                                'required': False,
                                'default': False,
                                'description': 'Return source XML/CSV data'
                            },{
                                'name': 'page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 0
                            },{
                                'name': 'per_page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 10
                            }
                        ],
                        'responses': {
                            200: {
                                'description': 'A list of copyright registrations and renewals',
                                'schema': {
                                    '$ref': '#/definitions/MultiResponse'
                                }
                            }
                        }
                    }
                },
                '/search/registration/{regnum}': {
                    'get': {
                        'tags': ['Search'],
                        'summary': 'Returns a set of registration and renewal objects',
                        'description': 'Accepts a copyright registration number and returns all matching records',
                        'parameters': [
                            {
                                'name': 'regnum',
                                'in': 'path',
                                'required': True,
                                'schema': {
                                    'type': 'string'
                                },
                                'description': 'Standard copyright registration number'
                            },{
                                'name': 'source',
                                'in': 'query',
                                'type': 'boolean',
                                'required': False,
                                'default': False,
                                'description': 'Return source XML/CSV data'
                            },{
                                'name': 'page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 0
                            },{
                                'name': 'per_page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 10
                            }
                        ],
                        'responses': {
                            200: {
                                'description': 'A list of copyright registrations and renewals',
                                'schema': {
                                    '$ref': '#/definitions/MultiResponse'
                                }
                            }
                        }
                    }
                },
                '/search/renewal/{rennum}': {
                    'get': {
                        'tags': ['Search'],
                        'summary': 'Returns a set of registration and renewal objects',
                        'description': 'Accepts a copyright renewal number and returns all matching records',
                        'parameters': [
                            {
                                'name': 'rennum',
                                'in': 'path',
                                'required': True,
                                'schema': {
                                    'type': 'string'
                                },
                                'description': 'Standard copyright renewal number'
                            },{
                                'name': 'source',
                                'in': 'query',
                                'type': 'boolean',
                                'required': False,
                                'default': False,
                                'description': 'Return source XML/CSV data'
                            },{
                                'name': 'page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 0
                            },{
                                'name': 'per_page',
                                'in': 'query',
                                'type': 'number',
                                'required': False,
                                'default': 10
                            }
                        ],
                        'responses': {
                            200: {
                                'description': 'A list of copyright registrations and renewals',
                                'schema': {
                                    '$ref': '#/definitions/MultiResponse'
                                }
                            }
                        }
                    }
                },
                '/registration/{uuid}': {
                    'get': {
                        'tags': ['Lookup'],
                        'summary': 'Return a specific Registration record by UUID',
                        'description': 'Accepts a UUID and returns a registration record',
                        'parameters': [{
                            'name': 'uuid',
                            'in': 'path',
                            'required': True,
                            'schema': {
                                'type': 'string'
                            },
                            'description': 'Standard UUID'
                        }],
                        'responses': {
                            200: {
                                'description': 'A single Registration record',
                                'schema': {
                                    '$ref': '#/definitions/SingleResponse'
                                }
                            },
                            404: {
                                'description': 'A message noting that the UUID could not be found',
                                'schema': {
                                    '$ref': '#/definitions/ErrorResponse'
                                }
                            },
                            500: {
                                'description': 'Generic internal error message',
                                'schema': {
                                    '$ref': '#/definitions/ErrorResponse'
                                }
                            }
                        }
                    }
                },
                '/renewal/{uuid}': {
                    'get': {
                        'tags': ['Lookup'],
                        'summary': 'Return a specific Renewal record by UUID',
                        'description': 'Accepts a UUID and returns either an orphan renewal record or the parent registration with associated renewals',
                        'parameters': [{
                            'name': 'uuid',
                            'in': 'path',
                            'required': True,
                            'schema': {
                                'type': 'string'
                            },
                            'description': 'Standard UUID'
                        }],
                        'responses': {
                            200: {
                                'description': 'A single Renewal or Registration record',
                                'schema': {
                                    '$ref': '#/definitions/SingleResponse'
                                }
                            },
                            404: {
                                'description': 'A message noting that the UUID could not be found',
                                'schema': {
                                    '$ref': '#/definitions/ErrorResponse'
                                }
                            },
                            500: {
                                'description': 'Generic internal error message',
                                'schema': {
                                    '$ref': '#/definitions/ErrorResponse'
                                }
                            }
                        }
                    }
                }
            },
            'definitions': {
                'ErrorResponse': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'integer'
                        },
                        'message': {
                            'type': 'string'
                        }
                    }
                },
                'SingleResponse': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'integer'
                        },
                        'data': {
                            'type': 'object',
                            'anyOf': [
                                {'$ref': '#/definitions/Registration'},
                                {'$ref': '#/definitions/Renewal'}
                            ]
                        }
                    }
                },
                'MultiResponse': {
                    'type': 'object',
                    'properties': {
                        'total': {
                            'type': 'integer',
                        },
                        'query': {
                            'type': 'object',
                            '$ref': '#/definitions/Query'
                        },
                        'paging': {
                            'type': 'object',
                            '$ref': '#/definitions/Paging'
                        },
                        'results': {
                            'type': 'array',
                            'items': {
                                'anyOf': [
                                    {'$ref': '#/definitions/Registration'},
                                    {'$ref': '#/definitions/Renewal'}
                                ]
                            }
                        }
                    }
                },
                'Query': {
                    'type': 'object',
                    'properties': {
                        'endpoint': {
                            'type': 'string'
                        },
                        'term': {
                            'type': 'string'
                        }
                    }
                },
                'Paging': {
                    'type': 'object',
                    'properties': {
                        'first': {
                            'type': 'string'
                        },
                        'previous': {
                            'type': 'string'
                        },
                        'next': {
                            'type': 'string'
                        },
                        'last': {
                            'type': 'string'
                        }
                    }
                },
                'Registration': {
                    'type': 'object', 
                    'properties': {
                        'title': {
                            'type': 'string'
                        },
                        'copies': {
                            'type': 'string'
                        }, 
                        'copy_date': {
                            'type': 'string'
                        }, 
                        'description': {
                            'type': 'string'
                        },
                        'authors': {
                            'type': 'array', 
                            'items': {
                                '$ref': '#/definitions/Agent'
                            }
                        },
                        'publishers': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/Agent'
                            }
                        }, 
                        'registrations': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/RegRegistration'
                            }
                        }, 
                        'renewals':{
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/Renewal'
                            }
                        },
                        'source': {
                            'type': 'object',
                            'properties': {
                                'page': {
                                    'type': 'integer'
                                }, 
                                'page_position': {
                                    'type': 'integer'
                                }, 
                                'part': {
                                    'type': 'string'
                                }, 
                                'series': {
                                    'type': 'string'
                                }, 
                                'url': {
                                    'type': 'string'
                                }, 
                                'year': {
                                    'type': 'integer'
                                }
                            }
                        }
                    }
                }, 
                'Agent': {
                    'type': 'string'
                }, 
                'RegRegistration': {
                    'type': 'object', 
                    'properties': {
                        'number': {
                            'type': 'string'
                        }, 
                        'date': {
                            'type': 'string'
                        }
                    }
                },
                'Renewal': {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string'
                        },
                        'title': {
                            'type': 'string'
                        },
                        'author': {
                            'type': 'string'
                        },
                        'new_matter': {
                            'type': 'string'
                        },
                        'renewal_num': {
                            'type': 'string'
                        },
                        'renewal_date': {
                            'type': 'string'
                        },
                        'notes': {
                            'type': 'string'
                        },
                        'volume': {
                            'type': 'string'
                        },
                        'part': {
                            'type': 'string'
                        },
                        'number': {
                            'type': 'string'
                        },
                        'page': {
                            'type': 'string'
                        },
                        'claimants': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/Claimant'
                            }
                        }
                    }
                },
                'Claimant': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string'
                        },
                        'type': {
                            'type': 'string'
                        }
                    }
                }
            }
        }