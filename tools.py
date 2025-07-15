def get_tools_schema():
    """
    Returns a list of tools (functions) the AI can use, formatted as a JSON schema.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_mandi_price",
                "description": "Used to fetch the current market price for a single crop in a specific district.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "district": { "type": "string" },
                        "crop": { "type": "string" },
                    },
                    "required": ["district", "crop"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_revenue_estimate",
                "description": "Calculates total estimated revenue when the user provides a crop, district, and area in acres.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "district": { "type": "string" },
                        "crop": { "type": "string" },
                        "area": { "type": "number", "description": "The area in acres." }
                    },
                    "required": ["district", "crop", "area"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_fertilizer_plan",
                "description": "Use this tool any time the user asks to create a fertilizer plan. It can be used with or without a specific report ID.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "report_id": {
                            "type": "integer",
                            "description": "The specific ID of the report to generate a plan from, if the user provides one."
                        }
                    }, 
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_my_reports",
                "description": "Use this when the user asks to see their reports, history, generate fertilizer plan or their 'latest' analysis. This tool lists recent reports for viewing.",
                "parameters": { "type": "object", "properties": {} }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_specific_report",
                "description": "Use this ONLY when the user asks to view the details of a report and provides a specific, numeric Report ID.",
                "parameters": {
                    "type": "object",
                    "properties": { "report_id": { "type": "integer" } },
                    "required": ["report_id"]
                }
            }
        }
    ]
    return tools