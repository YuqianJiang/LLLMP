
select_schema = {
    "name": "select",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "number"
                        },
                        "description": {
                            "type": "string"
                        },
                        "candidates": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "multi_match": {
                            "type": "boolean",
                            "description": "set to true if this description is in the context of multiple entities, including each, all, smallest"
                        }
                    },
                    "required": ["id", "description", "candidates", "multi_match"],
                    "additionalProperties": False
                }
            },
            "relationships": {
                "type": "array",
                "items": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "entity": {
                                    "type": "number"
                                },
                                "predicate": {
                                    "type": "string",
                                    "enum": ["phone_ringing", "window_open", "tv_on", "light_on", "faucet_on",
                                             "dish_is_clean",
                                             "cloth_is_clean", "cloth_is_dry", "glass_empty"]
                                },
                                "value": {
                                    "type": "boolean"
                                }
                            },
                            "required": ["entity", "predicate", "value"],
                            "additionalProperties": False
                        },
                        {
                            "type": "object",
                            "properties": {
                                "subject": {
                                    "type": "number"
                                },
                                "predicate": {
                                    "type": "string",
                                    "enum": ["in_person_hand", "person_in_room", "room_has", "placed_at_table",
                                             "placed_at_washer", "placed_at_laundrybasket", "placed_at_kitchensink",
                                             "placed_at_fridge", "placed_at_dryer", "placed_at_shelf",
                                             "shelf_has_level", "on_shelf_level", "tv_playing_channel",
                                             "glass_has_liquid", "in_agent_hand", "agent_in_room"]
                                },
                                "object": {
                                    "type": "number"
                                }
                            },
                            "required": ["subject", "predicate", "object"],
                            "additionalProperties": False
                        },
                        {
							"type": "null"
						}
                    ]
                },
                "description": "implied relationships before the described change or task, do not assume anything if such information is missing"
            }
        },
        "required": ["entities", "relationships"],
        "additionalProperties": False
    }
}
'''
select_schema = {
    "name": "select",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "number"
                        },
                        "description": {
                            "type": "string"
                        },
                        "candidates": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "multi_match": {
                            "type": "boolean",
                            "description": "set to true if this description is in the context of multiple objects, including each, all, smallest"
                        }
                    },
                    "required": ["id", "description", "candidates", "multi_match"],
                    "additionalProperties": False
                }
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "number"
                        },
                        "predicate": {
                            "type": "string",
                            "enum": ["phone_ringing", "window_open", "tv_on", "light_on", "faucet_on",
                                     "dish_is_clean", "cloth_is_clean", "cloth_is_dry", "glass_empty",
                                     "in_person_hand", "person_in_room", "room_has", "placed_at_table",
                                     "placed_at_washer", "placed_at_laundrybasket", "placed_at_kitchensink",
                                     "placed_at_fridge", "placed_at_dryer", "placed_at_shelf",
                                     "shelf_has_level", "on_shelf_level", "tv_playing_channel",
                                     "glass_has_liquid", "in_agent_hand", "agent_in_room"
                                     ]
                        },
                        "object": {
                            "type": ["boolean", "number"]
                        }
                    },
                    "required": ["subject", "predicate", "object"],
                    "additionalProperties": False
                },
                "description": "implied relationships before the described change or task, do not assume anything else"
            }
        },
        "required": ["entities", "relationships"],
        "additionalProperties": False
    }
}
'''
update_schema = {
    "name": "update",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string"
                        },
                        "predicate": {
                            "type": "string",
                            "enum": ["phone_ringing", "window_open", "tv_on", "light_on", "faucet_on",
                                     "dish_is_clean", "cloth_is_clean", "cloth_is_dry", "glass_empty",
                                     "in_person_hand", "person_in_room", "room_has", "placed_at_table",
                                     "placed_at_washer", "placed_at_laundrybasket", "placed_at_kitchensink",
                                     "placed_at_fridge", "placed_at_dryer", "placed_at_shelf",
                                     "shelf_has_level", "on_shelf_level", "tv_playing_channel",
                                     "glass_has_liquid", "in_agent_hand", "agent_in_room"
                                     ]
                        },
                        "object": {
                            "type": ["boolean", "string"]
                        },
                        "action": {
                            "type": "string",
                            "enum": ["add", "delete", "update"]
                        }
                    },
                    "required": ["subject", "predicate", "object", "action"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["relationships"],
        "additionalProperties": False
    }
}

goal_schema = {
    "name": "goal",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string"
                        },
                        "predicate": {
                            "type": "string",
                            "enum": ["phone_ringing", "window_open", "tv_on", "light_on", "faucet_on",
                                     "dish_is_clean", "cloth_is_clean", "cloth_is_dry", "glass_empty",
                                     "in_person_hand", "person_in_room", "room_has", "placed_at_table",
                                     "placed_at_washer", "placed_at_laundrybasket", "placed_at_kitchensink",
                                     "placed_at_fridge", "placed_at_dryer", "placed_at_shelf",
                                     "shelf_has_level", "on_shelf_level", "tv_playing_channel",
                                     "glass_has_liquid", "in_agent_hand", "agent_in_room"
                                     ]
                        },
                        "object": {
                            "type": ["boolean", "string"]
                        }
                    },
                    "required": ["subject", "predicate", "object", "action"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["relationships"],
        "additionalProperties": False
    }
}