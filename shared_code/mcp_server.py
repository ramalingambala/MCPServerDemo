"""
Shared MCP Server Code for Azure Functions
This module contains the core MCP server functionality that can be used 
across different Azure Function triggers.
"""

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP not available: {e}")
    MCP_AVAILABLE = False

import math
import os
import json
from typing import Dict, List, Union, Optional
import logging

# Configure logging for Azure Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP (Model Context Protocol) server instance with descriptive name
if MCP_AVAILABLE:
    try:
        mcp = FastMCP("BMI & SQL Server - Azure Functions")
        logger.info("FastMCP server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FastMCP: {e}")
        MCP_AVAILABLE = False
        mcp = None
else:
    logger.error("MCP not available - FastMCP will not be initialized")
    mcp = None

# Create a dummy decorator for when MCP is not available


def dummy_tool(*args, **kwargs):
    def decorator(func):
        logger.warning(
            f"MCP not available - skipping tool registration for {func.__name__}")
        return func
    return decorator


# If MCP is not available, replace mcp.tool with dummy decorator
if not MCP_AVAILABLE or mcp is None:
    class DummyMCP:
        def __init__(self):
            pass

        def tool(self, *args, **kwargs):
            return dummy_tool(*args, **kwargs)

        def resource(self, *args, **kwargs):
            return dummy_tool(*args, **kwargs)

        def list_tools(self):
            return []

        def call_tool(self, name, arguments):
            raise Exception("MCP not available")

    mcp = DummyMCP()

# SQL Server Configuration - Use environment variables for Azure deployment security
CURRENT_SQL_CONFIG = os.environ.get("SQL_CONFIG", "azure_production")


# BMI Resources - Static information for BMI calculations
BMI_CATEGORIES = {
    "underweight": {"range": "< 18.5", "description": "Below normal weight"},
    "normal": {"range": "18.5 - 24.9", "description": "Normal weight"},
    "overweight": {"range": "25.0 - 29.9", "description": "Above normal weight"},
    "obese_class_1": {"range": "30.0 - 34.9", "description": "Obesity Class I (Moderately obese)"},
    "obese_class_2": {"range": "35.0 - 39.9", "description": "Obesity Class II (Severely obese)"},
    "obese_class_3": {"range": "≥ 40.0", "description": "Obesity Class III (Very severely obese)"}
}

BMI_HEALTH_RISKS = {
    "underweight": [
        "Increased risk of malnutrition",
        "Weakened immune system",
        "Increased risk of infections",
        "Delayed wound healing",
        "Loss of bone density"
    ],
    "normal": [
        "Lowest risk of weight-related health problems",
        "Optimal health range for most people"
    ],
    "overweight": [
        "Increased risk of type 2 diabetes",
        "Increased risk of high blood pressure",
        "Increased risk of heart disease",
        "Sleep apnea risk"
    ],
    "obese": [
        "High risk of type 2 diabetes",
        "High risk of cardiovascular disease",
        "Increased risk of certain cancers",
        "Sleep apnea and breathing problems",
        "Osteoarthritis",
        "Fatty liver disease",
        "Kidney disease"
    ]
}


# MCP Resources for BMI Calculator
@mcp.resource("bmi://categories")
def bmi_categories_resource() -> str:
    """
    BMI Categories and Ranges Resource

    Provides WHO standard BMI categories with ranges and descriptions.
    This resource contains the official BMI classification system used
    by healthcare professionals worldwide.
    """
    return json.dumps({
        "title": "WHO BMI Categories and Ranges",
        "description": "Official Body Mass Index categories as defined by the World Health Organization",
        "last_updated": "2024",
        "source": "World Health Organization",
        "categories": BMI_CATEGORIES
    }, indent=2)


@mcp.resource("bmi://health-risks")
def bmi_health_risks_resource() -> str:
    """
    BMI Health Risks Resource

    Provides information about health risks associated with different BMI categories.
    This resource helps users understand the potential health implications
    of their BMI results.
    """
    return json.dumps({
        "title": "Health Risks Associated with BMI Categories",
        "description": "Medical information about health risks for different BMI ranges",
        "disclaimer": "This information is for educational purposes only and should not replace professional medical advice",
        "last_updated": "2024",
        "health_risks": BMI_HEALTH_RISKS
    }, indent=2)


@mcp.resource("bmi://calculation-guide")
def bmi_calculation_guide_resource() -> str:
    """
    BMI Calculation Guide Resource

    Provides detailed information about BMI calculation methods,
    formula explanation, and unit conversions.
    """
    guide = {
        "title": "BMI Calculation Guide",
        "description": "Complete guide to calculating Body Mass Index",
        "formula": {
            "metric": "BMI = weight (kg) / height (m)²",
            "imperial": "BMI = (weight (lbs) / height (inches)²) × 703"
        },
        "unit_conversions": {
            "weight": {
                "pounds_to_kg": "pounds ÷ 2.205",
                "kg_to_pounds": "kg × 2.205"
            },
            "height": {
                "inches_to_meters": "inches × 0.0254",
                "feet_inches_to_meters": "(feet × 12 + inches) × 0.0254",
                "cm_to_meters": "cm ÷ 100"
            }
        },
        "examples": [
            {
                "description": "Person weighing 70kg and 1.75m tall",
                "calculation": "70 ÷ (1.75)² = 70 ÷ 3.0625 = 22.86",
                "category": "Normal weight"
            },
            {
                "description": "Person weighing 154lbs and 5'9\" tall",
                "calculation": "(154 ÷ 69²) × 703 = (154 ÷ 4761) × 703 = 22.74",
                "category": "Normal weight"
            }
        ],
        "limitations": [
            "Does not distinguish between muscle and fat mass",
            "May not be accurate for athletes with high muscle mass",
            "Age and gender are not considered",
            "May not be suitable for pregnant women",
            "Children and adolescents require different calculations"
        ]
    }

    return json.dumps(guide, indent=2)


@mcp.resource("bmi://healthy-weight-tips")
def bmi_healthy_weight_tips_resource() -> str:
    """
    Healthy Weight Management Tips Resource

    Provides evidence-based tips for maintaining a healthy weight
    and improving overall health across different BMI categories.
    """
    tips = {
        "title": "Healthy Weight Management Tips",
        "description": "Evidence-based recommendations for achieving and maintaining a healthy weight",
        "general_tips": [
            "Eat a balanced diet rich in fruits, vegetables, whole grains, and lean proteins",
            "Stay hydrated by drinking plenty of water throughout the day",
            "Engage in regular physical activity (at least 150 minutes of moderate exercise per week)",
            "Get adequate sleep (7-9 hours per night for adults)",
            "Manage stress through healthy coping mechanisms",
            "Monitor portion sizes and practice mindful eating"
        ],
        "category_specific_advice": {
            "underweight": [
                "Consult with a healthcare provider to rule out underlying conditions",
                "Focus on nutrient-dense, calorie-rich foods",
                "Include healthy fats like nuts, avocados, and olive oil",
                "Consider strength training to build muscle mass",
                "Eat frequent, smaller meals throughout the day"
            ],
            "normal": [
                "Maintain current healthy habits",
                "Continue regular exercise routine",
                "Monitor weight regularly but don't obsess",
                "Focus on overall health rather than just weight"
            ],
            "overweight": [
                "Create a modest caloric deficit through diet and exercise",
                "Increase physical activity gradually",
                "Focus on sustainable lifestyle changes",
                "Consider working with a registered dietitian",
                "Track food intake to identify patterns"
            ],
            "obese": [
                "Consult with healthcare professionals for a comprehensive plan",
                "Consider medical evaluation for weight-related health conditions",
                "Focus on gradual, sustainable weight loss (1-2 pounds per week)",
                "May benefit from structured weight loss programs",
                "Address emotional and behavioral factors related to eating"
            ]
        },
        "when_to_seek_help": [
            "BMI below 18.5 or above 30",
            "Rapid unexplained weight changes",
            "Difficulty losing weight despite lifestyle changes",
            "Weight-related health problems",
            "Eating disorders or unhealthy relationships with food"
        ]
    }

    return json.dumps(tips, indent=2)


def get_sql_config():
    """
    Get SQL configuration from environment variables

    Returns a dictionary containing SQL Server connection parameters
    loaded from Azure Functions application settings (environment variables).
    This approach follows security best practices by avoiding hardcoded credentials.

    Returns:
        dict: SQL Server configuration parameters
    """
    return {
        'server': os.environ.get('SQL_SERVER', 'upskilling-dbserver.database.windows.net'),
        'database': os.environ.get('SQL_DATABASE', 'TestDB'),
        'username': os.environ.get('SQL_USERNAME', ''),
        'password': os.environ.get('SQL_PASSWORD', ''),
        'driver': os.environ.get('SQL_DRIVER', 'ODBC Driver 18 for SQL Server'),
        # Default to Managed Identity
        'authentication': os.environ.get('SQL_AUTH_TYPE', 'ActiveDirectoryMsi'),
        'timeout': int(os.environ.get('SQL_TIMEOUT', '30')),
        'encrypt': os.environ.get('SQL_ENCRYPT', 'yes'),
        'trust_server_certificate': os.environ.get('SQL_TRUST_CERT', 'no')
    }


def get_connection_string(use_tcp=True) -> str:
    """
    Generate SQL Server connection string from environment variables

    Creates a properly formatted ODBC connection string based on the
    authentication method. Supports:
    - ActiveDirectoryMsi: Azure Managed Identity (recommended for Azure Functions)
    - SqlPassword: SQL Server Authentication (username/password)
    - ActiveDirectoryIntegrated: Windows Authentication

    Args:
        use_tcp: Whether to use TCP/IP protocol (ignored for Azure SQL)

    Returns:
        str: Formatted ODBC connection string
    """
    config = get_sql_config()
    auth_type = config['authentication']

    # Base connection parameters
    base_params = (
        f"DRIVER={{{config['driver']}}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"Encrypt={config['encrypt']};"
        f"TrustServerCertificate={config['trust_server_certificate']};"
        f"Connection Timeout={config['timeout']};"
    )

    if auth_type == 'ActiveDirectoryMsi':
        # Use Azure Managed Identity (recommended for Azure Functions)
        connection_string = (
            base_params +
            "Authentication=ActiveDirectoryMsi;"
        )
    elif auth_type == 'SqlPassword':
        # Use SQL Server Authentication with username/password
        connection_string = (
            base_params +
            f"UID={config['username']};"
            f"PWD={config['password']};"
        )
    elif auth_type == 'ActiveDirectoryIntegrated':
        # Use Windows Authentication
        connection_string = (
            base_params +
            "Authentication=ActiveDirectoryIntegrated;"
        )
    elif auth_type == 'ActiveDirectoryInteractive':
        # Use interactive Azure AD authentication (not suitable for Azure Functions)
        connection_string = (
            base_params +
            "Authentication=ActiveDirectoryInteractive;"
        )
    else:
        # Fallback to SQL authentication for unknown types
        logger.warning(
            f"Unknown authentication type: {auth_type}. Falling back to SQL authentication.")
        connection_string = (
            base_params +
            f"UID={config['username']};"
            f"PWD={config['password']};"
        )

    return connection_string


@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """
    Calculate BMI given weight in kilograms and height in meters

    Calculates Body Mass Index (BMI) using the standard formula: weight / height²
    Also categorizes the BMI result according to WHO standards and provides
    relevant health information and recommendations.

    Related resources:
    - bmi://categories: BMI categories and ranges
    - bmi://health-risks: Health risks by BMI category  
    - bmi://calculation-guide: Detailed calculation guide
    - bmi://healthy-weight-tips: Weight management tips

    Args:
        weight_kg: Weight in kilograms (must be positive)
        height_m: Height in meters (must be positive)

    Returns:
        JSON string with BMI calculation result, category, health risks, and recommendations
    """
    try:
        # Input validation - ensure positive values
        if height_m <= 0 or weight_kg <= 0:
            result = {
                "error": "Height and weight must be positive numbers",
                "weight_kg": weight_kg,
                "height_m": height_m,
                "resources": {
                    "calculation_guide": "bmi://calculation-guide",
                    "categories": "bmi://categories"
                }
            }
            return json.dumps(result, indent=2)

        # Calculate BMI using standard formula
        bmi = weight_kg / (height_m ** 2)

        # Determine detailed BMI category
        if bmi < 18.5:
            category = "Underweight"
            category_key = "underweight"
            category_range = "< 18.5"
        elif bmi < 25:
            category = "Normal weight"
            category_key = "normal"
            category_range = "18.5 - 24.9"
        elif bmi < 30:
            category = "Overweight"
            category_key = "overweight"
            category_range = "25.0 - 29.9"
        elif bmi < 35:
            category = "Obesity Class I"
            category_key = "obese"
            category_range = "30.0 - 34.9"
        elif bmi < 40:
            category = "Obesity Class II"
            category_key = "obese"
            category_range = "35.0 - 39.9"
        else:
            category = "Obesity Class III"
            category_key = "obese"
            category_range = "≥ 40.0"

        # Get health risks for the category
        health_risks = BMI_HEALTH_RISKS.get(category_key, [])

        # Calculate healthy weight range for the person's height
        healthy_min = 18.5 * (height_m ** 2)
        healthy_max = 24.9 * (height_m ** 2)

        # Prepare comprehensive result with all relevant information
        result = {
            "bmi": round(bmi, 2),
            "category": category,
            "category_range": category_range,
            "weight_kg": weight_kg,
            "height_m": height_m,
            "calculation": f"{weight_kg} / ({height_m})² = {bmi:.2f}",
            "healthy_weight_range": {
                "min_kg": round(healthy_min, 1),
                "max_kg": round(healthy_max, 1),
                "description": f"For your height ({height_m}m), a healthy weight range is {round(healthy_min, 1)}-{round(healthy_max, 1)} kg"
            },
            "health_information": {
                "risks": health_risks,
                "interpretation": BMI_CATEGORIES.get(category_key.replace("obese", "obese_class_1"), {}).get("description", "")
            },
            "recommendations": {
                "consult_healthcare": bmi < 18.5 or bmi >= 30,
                "lifestyle_focus": "Maintain a balanced diet and regular physical activity",
                "monitoring": "Regular BMI monitoring can help track health progress"
            },
            "resources": {
                "categories": "bmi://categories",
                "health_risks": "bmi://health-risks",
                "calculation_guide": "bmi://calculation-guide",
                "healthy_weight_tips": "bmi://healthy-weight-tips"
            },
            "disclaimer": "This BMI calculation is for informational purposes only and should not replace professional medical advice. Consult healthcare professionals for personalized health recommendations."
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        # Handle any unexpected errors gracefully
        result = {
            "error": str(e),
            "weight_kg": weight_kg,
            "height_m": height_m,
            "resources": {
                "calculation_guide": "bmi://calculation-guide",
                "categories": "bmi://categories"
            }
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def get_bmi_resources(resource_type: str = "all") -> str:
    """
    Get BMI-related resources and information

    Provides access to comprehensive BMI information including categories,
    health risks, calculation guides, and healthy weight management tips.

    Args:
        resource_type: Type of resource to retrieve. Options:
                      - "all": All BMI resources
                      - "categories": BMI categories and ranges
                      - "health-risks": Health risks by BMI category
                      - "calculation-guide": Detailed calculation guide
                      - "healthy-weight-tips": Weight management tips

    Returns:
        JSON string with requested BMI resource information
    """
    try:
        if resource_type == "categories":
            return bmi_categories_resource()
        elif resource_type == "health-risks":
            return bmi_health_risks_resource()
        elif resource_type == "calculation-guide":
            return bmi_calculation_guide_resource()
        elif resource_type == "healthy-weight-tips":
            return bmi_healthy_weight_tips_resource()
        elif resource_type == "all":
            # Return all resources in a structured format
            all_resources = {
                "bmi_resources": {
                    "categories": json.loads(bmi_categories_resource()),
                    "health_risks": json.loads(bmi_health_risks_resource()),
                    "calculation_guide": json.loads(bmi_calculation_guide_resource()),
                    "healthy_weight_tips": json.loads(bmi_healthy_weight_tips_resource())
                },
                "resource_uris": [
                    "bmi://categories",
                    "bmi://health-risks",
                    "bmi://calculation-guide",
                    "bmi://healthy-weight-tips"
                ]
            }
            return json.dumps(all_resources, indent=2)
        else:
            # Invalid resource type
            result = {
                "error": f"Invalid resource type: {resource_type}",
                "valid_types": ["all", "categories", "health-risks", "calculation-guide", "healthy-weight-tips"],
                "available_resources": [
                    "bmi://categories",
                    "bmi://health-risks",
                    "bmi://calculation-guide",
                    "bmi://healthy-weight-tips"
                ]
            }
            return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "error": str(e),
            "resource_type": resource_type
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def test_network_connectivity() -> str:
    """
    Test network connectivity to the SQL Server

    Performs a low-level TCP connection test to verify if the SQL Server
    is reachable from the Azure Functions environment. This is useful
    for troubleshooting network connectivity issues.

    Returns:
        JSON string with connectivity test results including response time
    """
    import socket
    import time

    config = get_sql_config()
    server_host = config['server']
    port = 1433  # Default SQL Server port

    # Initialize result structure
    result = {
        "server": server_host,
        "port": port,
        "reachable": False,
        "response_time_ms": None,
        "error": None
    }

    try:
        # Perform TCP connection test with timing
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout to prevent hanging

        # Attempt connection (non-blocking test)
        connection_result = sock.connect_ex((server_host, port))
        end_time = time.time()

        # Clean up socket connection
        sock.close()

        if connection_result == 0:
            # Connection successful
            result["reachable"] = True
            result["response_time_ms"] = round(
                (end_time - start_time) * 1000, 2)
        else:
            # Connection failed
            result["error"] = f"Connection failed with code: {connection_result}"

    except Exception as e:
        # Handle network errors (DNS resolution, etc.)
        result["error"] = str(e)

    return json.dumps(result, indent=2)


@mcp.tool()
def test_sql_connection() -> str:
    """
    Test the SQL Server connection and return connection status

    Performs a full database connection test using the configured
    connection string. Executes a simple query to verify both
    connectivity and authentication.

    Returns:
        JSON string with connection status and server information
    """
    try:
        import pyodbc
        connection_string = get_connection_string()

        logger.info(
            f"Testing connection with authentication: {get_sql_config()['authentication']}")

        # Establish database connection
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        # Execute test query to verify connection and get server info
        cursor.execute(
            "SELECT @@VERSION as server_version, DB_NAME() as database_name")
        row = cursor.fetchone()

        # Prepare success result with server information
        result = {
            "status": "success",
            "connected": True,
            "server_version": str(row[0]) if row else "Unknown",
            "database_name": str(row[1]) if row else "Unknown",
            "server": get_sql_config()['server'],
            "database": get_sql_config()['database'],
            "authentication_type": get_sql_config()['authentication']
        }

        # Clean up database resources
        cursor.close()
        cnxn.close()
        return json.dumps(result, indent=2)

    except Exception as e:
        # Handle connection errors (authentication, network, etc.)
        logger.error(f"SQL connection test failed: {str(e)}")
        config = get_sql_config()
        result = {
            "status": "error",
            "connected": False,
            "error": str(e),
            "server": config['server'],
            "database": config['database'],
            "authentication_type": config['authentication'],
            "connection_string_sample": get_connection_string().replace(config.get('password', ''), '***') if config.get('password') else get_connection_string()
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def query_sql_server(query: str) -> str:
    """
    Executes a read-only SQL SELECT query against a SQL Server database
    and returns the results as JSON.

    Security measures implemented:
    - Only SELECT statements allowed
    - Blocks dangerous SQL keywords (DROP, DELETE, etc.)
    - Returns results in a structured JSON format

    Args:
        query: SQL SELECT query to execute (must be read-only)

    Returns:
        JSON string with query results or error information
    """
    # Security validation - only allow SELECT statements
    query_trimmed = query.strip().upper()
    if not query_trimmed.startswith('SELECT'):
        return json.dumps({"error": "Only SELECT queries are allowed for security reasons"}, indent=2)

    # Additional security check - block dangerous SQL keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT',
                          'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    if any(keyword in query_trimmed for keyword in dangerous_keywords):
        return json.dumps({"error": "Query contains potentially dangerous keywords. Only SELECT queries are allowed."}, indent=2)

    try:
        import pyodbc
        connection_string = get_connection_string()

        logger.info(
            f"Attempting to connect with authentication: {get_sql_config()['authentication']}")

        # Establish database connection
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        # Execute the user-provided query
        cursor.execute(query)

        # Extract column names from cursor metadata
        columns = [column[0]
                   for column in cursor.description] if cursor.description else []

        # Fetch and process all results
        results = []
        rows = cursor.fetchall()

        for row in rows:
            # Convert each row to a dictionary for JSON serialization
            row_dict = {}
            for i, value in enumerate(row):
                # Handle different data types appropriately
                if value is None:
                    row_dict[columns[i]] = None
                elif isinstance(value, (int, float, str, bool)):
                    row_dict[columns[i]] = value
                else:
                    # Convert complex types to string representation
                    row_dict[columns[i]] = str(value)
            results.append(row_dict)

        # Clean up database resources
        cursor.close()
        cnxn.close()

        # Prepare successful result with metadata and data
        result = {
            "status": "success",
            "row_count": len(results),
            "columns": columns,
            "data": results,
            "authentication_used": get_sql_config()['authentication']
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        # Handle query execution errors
        logger.error(f"SQL query failed: {str(e)}")
        config = get_sql_config()
        result = {
            "status": "error",
            "error": str(e),
            "query": query,
            "server": config['server'],
            "database": config['database'],
            "authentication_type": config['authentication'],
            "connection_string_sample": get_connection_string().replace(config.get('password', ''), '***') if config.get('password') else get_connection_string()
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def get_sql_config_debug() -> str:
    """
    Get detailed SQL Server configuration for debugging

    Returns current SQL configuration, connection string (with redacted password),
    and environment variables to help diagnose connection issues.

    Returns:
        JSON string with SQL configuration details
    """
    config = get_sql_config()
    connection_string = get_connection_string()

    # Redact password from connection string for security
    redacted_connection_string = connection_string
    if config.get('password'):
        redacted_connection_string = connection_string.replace(
            config['password'], '***REDACTED***')

    result = {
        "sql_configuration": {
            "server": config['server'],
            "database": config['database'],
            "authentication_type": config['authentication'],
            "driver": config['driver'],
            "timeout": config['timeout'],
            "encrypt": config['encrypt'],
            "trust_server_certificate": config['trust_server_certificate']
        },
        "connection_string": redacted_connection_string,
        "environment_variables": {
            "SQL_SERVER": os.environ.get('SQL_SERVER', 'NOT_SET'),
            "SQL_DATABASE": os.environ.get('SQL_DATABASE', 'NOT_SET'),
            "SQL_AUTH_TYPE": os.environ.get('SQL_AUTH_TYPE', 'NOT_SET'),
            "SQL_USERNAME": os.environ.get('SQL_USERNAME', 'NOT_SET'),
            "SQL_PASSWORD": 'SET' if os.environ.get('SQL_PASSWORD') else 'NOT_SET',
            "SQL_DRIVER": os.environ.get('SQL_DRIVER', 'NOT_SET'),
            "SQL_TIMEOUT": os.environ.get('SQL_TIMEOUT', 'NOT_SET'),
            "SQL_ENCRYPT": os.environ.get('SQL_ENCRYPT', 'NOT_SET'),
            "SQL_TRUST_CERT": os.environ.get('SQL_TRUST_CERT', 'NOT_SET')
        },
        "recommendations": {
            "for_azure_functions": "Use SQL_AUTH_TYPE=ActiveDirectoryMsi for Azure Managed Identity",
            "required_setup": [
                "Enable System Managed Identity on Azure Function App",
                "Grant 'db_datareader' role to the Function App's managed identity in Azure SQL Database",
                "Set SQL_SERVER and SQL_DATABASE environment variables",
                "Set SQL_AUTH_TYPE=ActiveDirectoryMsi"
            ]
        }
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_server_info() -> str:
    """
    Get Azure Functions server information and environment details

    Retrieves runtime information about the Azure Functions environment,
    including function app details, region, and SQL configuration status.
    Useful for debugging and monitoring purposes.

    Returns:
        JSON string with comprehensive server and environment information
    """
    result = {
        "server_type": "Azure Functions",
        "python_version": os.environ.get('PYTHON_VERSION', 'Unknown'),
        "function_app_name": os.environ.get('WEBSITE_SITE_NAME', 'Unknown'),
        "resource_group": os.environ.get('WEBSITE_RESOURCE_GROUP', 'Unknown'),
        "subscription_id": os.environ.get('WEBSITE_SUBSCRIPTION_ID', 'Unknown'),
        "region": os.environ.get('WEBSITE_REGION_NAME', 'Unknown'),
        "sql_config": CURRENT_SQL_CONFIG,
        "environment_variables": {
            "sql_server": os.environ.get('SQL_SERVER', 'Not Set'),
            "sql_database": os.environ.get('SQL_DATABASE', 'Not Set'),
            "sql_auth_type": os.environ.get('SQL_AUTH_TYPE', 'Not Set')
        }
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def greet(name: str) -> str:
    """
    Get a personalized greeting from Azure Functions

    Simple greeting function to test MCP server functionality
    and demonstrate basic string parameter handling.

    Args:
        name: Name to include in the greeting

    Returns:
        Personalized greeting message
    """
    return f"Hello, {name}! Greetings from Azure Functions with MCP Server integration!"


# Export the MCP server instance and logger for use in Azure Functions
# These can be imported by Azure Function trigger files
__all__ = ['mcp', 'logger']
