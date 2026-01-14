"""
Agent-Native Search MCP Server

This server provides atomic tools for educational resource search.
Following agent-native principles: tools are primitives, not workflows.
The agent decides how to compose them to achieve search outcomes.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rule_based_search import RuleBasedSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchMCPServer:
    """MCP Server for agent-native educational resource search"""

    def __init__(self):
        self.engine = RuleBasedSearchEngine()
        self.search_history: List[Dict] = []

    # ============================================
    # Atomic Tools - Primitives, Not Workflows
    # ============================================

    def search(self, country: str, grade: str = "1", subject: str = "math",
               query: Optional[str] = None, max_results: int = 20) -> Dict:
        """
        Execute search with given parameters.

        This is a PRIMITIVE tool - it just searches.
        The AGENT decides when to search, what to search for, and how to use results.

        Args:
            query: Search query string
            country: Country code (ID, SA, CN, US, etc.)
            grade: Grade level (1, 2, 3, etc.)
            subject: Subject (math, science, etc.)
            max_results: Maximum results to return

        Returns:
            Search results with metadata
        """
        logger.info(f"Search: country={country}, grade={grade}, subject={subject}, query={query}")

        # Generate default query if not provided
        if query is None:
            # Generate query based on country, grade, and subject
            subject_names = {
                "math": "Matematika" if country.upper() == "ID" else "Mathematics",
                "science": "IPA" if country.upper() == "ID" else "Science",
                "english": "Bahasa Inggris" if country.upper() == "ID" else "English"
            }
            subject_name = subject_names.get(subject.lower(), subject.title())

            grade_names = {
                "ID": f"Kelas {grade}",
                "SA": f"الصف {grade}",
                "CN": f"{grade}年级",
                "US": f"Grade {grade}"
            }
            grade_name = grade_names.get(country.upper(), f"Grade {grade}")

            curriculum = "Kurikulum Merdeka" if country.upper() == "ID" else ""

            query_parts = [subject_name, grade_name]
            if curriculum:
                query_parts.append(curriculum)

            query = " ".join(query_parts)
            logger.info(f"Generated default query: {query}")

        try:
            result = self.engine.search(
                country=country,
                grade=grade,
                subject=subject,
                max_results=max_results
            )

            # Store in history for learning
            self.search_history.append({
                "query": query,
                "country": country,
                "grade": grade,
                "subject": subject,
                "results_count": len(result['results']),
                "supported": result['localized_info'].get('supported', False),
                "top_score": result['search_metadata'].get('top_score', 0)
            })

            return {
                "success": True,
                "results": result['results'],
                "localized_info": result['localized_info'],
                "search_metadata": result['search_metadata'],
                "text": f"Found {len(result['results'])} results for {country}-{grade}-{subject}"
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"Search failed: {e}",
                "results": []
            }

    def get_config(self, country: str) -> Dict:
        """
        Get configuration for a specific country.

        Returns what's configured for this country.
        The AGENT decides what to do with this information.

        Args:
            country: Country code

        Returns:
            Configuration information
        """
        logger.info(f"Get config: country={country}")

        try:
            # Get country config
            if country in self.engine.config:
                country_config = self.engine.config[country]
            else:
                # Try uppercase
                country_upper = country.upper()
                if country_upper in self.engine.config:
                    country_config = self.engine.config[country_upper]
                elif 'DEFAULT' in self.engine.config:
                    country_config = self.engine.config['DEFAULT']
                else:
                    return {
                        "success": False,
                        "text": f"No configuration found for country: {country}",
                        "configured": False
                    }

            # Extract key information
            grades_configured = []
            for key in country_config.keys():
                if key.startswith('grade_'):
                    grades_configured.append(key.replace('grade_', ''))

            return {
                "success": True,
                "country": country,
                "configured": True,
                "grades": grades_configured,
                "country_name": country_config.get('country_name', 'Unknown'),
                "language_code": country_config.get('language_code', 'en'),
                "text": f"Country {country} is configured with {len(grades_configured)} grades"
            }

        except Exception as e:
            logger.error(f"Get config failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"Failed to get config: {e}",
                "configured": False
            }

    def list_supported_countries(self) -> Dict:
        """
        List all supported countries.

        This is DYNAMIC CAPABILITY DISCOVERY.
        The agent learns what's available at runtime, not hardcoded.

        Returns:
            List of supported countries
        """
        logger.info("List supported countries")

        try:
            countries = []
            for code, config in self.engine.config.items():
                if code != 'DEFAULT':
                    countries.append({
                        "code": code,
                        "name": config.get('country_name', code),
                        "language": config.get('language_code', 'en')
                    })

            has_default = 'DEFAULT' in self.engine.config

            return {
                "success": True,
                "countries": countries,
                "has_default": has_default,
                "count": len(countries),
                "text": f"Found {len(countries)} configured countries" +
                       (f" plus DEFAULT config" if has_default else "")
            }

        except Exception as e:
            logger.error(f"List countries failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"Failed to list countries: {e}",
                "countries": []
            }

    def store_result(self, key: str, data: Any) -> Dict:
        """
        Store search result for later reference.

        This enables agent to learn and accumulate knowledge.

        Args:
            key: Storage key
            data: Data to store (will be JSON serialized)

        Returns:
            Storage result
        """
        logger.info(f"Store result: key={key}")

        try:
            # Store in workspace directory
            workspace_dir = Path(__file__).parent.parent / "agent_workspace"
            workspace_dir.mkdir(exist_ok=True)

            storage_file = workspace_dir / f"{key}.json"

            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "key": key,
                "path": str(storage_file),
                "text": f"Stored result under key: {key}"
            }

        except Exception as e:
            logger.error(f"Store result failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"Failed to store result: {e}"
            }

    def get_search_history(self, limit: int = 10) -> Dict:
        """
        Get recent search history.

        Helps agent learn from past searches.

        Args:
            limit: Maximum history items to return

        Returns:
            Recent search history
        """
        logger.info(f"Get search history: limit={limit}")

        try:
            recent = self.search_history[-limit:] if self.search_history else []

            return {
                "success": True,
                "history": recent,
                "count": len(recent),
                "total": len(self.search_history),
                "text": f"Retrieved {len(recent)} recent searches (total: {len(self.search_history)})"
            }

        except Exception as e:
            logger.error(f"Get history failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"Failed to get history: {e}",
                "history": []
            }

    def complete_task(self, summary: str, status: str = "success") -> Dict:
        """
        Signal task completion.

        This is the EXPLICIT COMPLETION SIGNAL pattern.
        The agent calls this when done.

        Args:
            summary: Summary of what was accomplished
            status: Task status (success, partial, blocked)

        Returns:
            Completion result with shouldContinue=False
        """
        logger.info(f"Complete task: status={status}")

        return {
            "success": True,
            "summary": summary,
            "status": status,
            "text": summary,
            "shouldContinue": False,  # Key: signals loop should stop
            "isComplete": True
        }

    # ============================================
    # Tool Registration (for MCP integration)
    # ============================================

    def list_tools(self) -> List[Dict]:
        """List available tools for agent discovery"""
        return [
            {
                "name": "search",
                "description": "Execute educational resource search with given parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Country code (ID, SA, CN, US, etc.)"
                        },
                        "grade": {
                            "type": "string",
                            "description": "Grade level (1, 2, 3, etc.)",
                            "default": "1"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Subject (math, science, etc.)",
                            "default": "math"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query string (optional, auto-generated if not provided)"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 20
                        }
                    },
                    "required": ["country"]
                }
            },
            {
                "name": "get_config",
                "description": "Get configuration for a specific country",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Country code"
                        }
                    },
                    "required": ["country"]
                }
            },
            {
                "name": "list_supported_countries",
                "description": "List all supported countries (dynamic capability discovery)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "store_result",
                "description": "Store search result for later reference",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Storage key"
                        },
                        "data": {
                            "type": "any",
                            "description": "Data to store (JSON serializable)"
                        }
                    },
                    "required": ["key", "data"]
                }
            },
            {
                "name": "get_search_history",
                "description": "Get recent search history",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum history items",
                            "default": 10
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "complete_task",
                "description": "Signal task completion (stops agent loop)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Summary of what was accomplished"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["success", "partial", "blocked"],
                            "description": "Task status",
                            "default": "success"
                        }
                    },
                    "required": ["summary"]
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict) -> Dict:
        """Execute a tool call"""
        logger.info(f"Tool call: {name} with {arguments}")

        tool_map = {
            "search": self.search,
            "get_config": self.get_config,
            "list_supported_countries": self.list_supported_countries,
            "store_result": self.store_result,
            "get_search_history": self.get_search_history,
            "complete_task": self.complete_task
        }

        if name not in tool_map:
            return {
                "success": False,
                "error": f"Unknown tool: {name}",
                "text": f"Tool '{name}' not found",
                "isError": True,
                "shouldContinue": True
            }

        try:
            return tool_map[name](**arguments)
        except TypeError as e:
            return {
                "success": False,
                "error": f"Invalid arguments for {name}: {e}",
                "text": f"Tool '{name}' called with invalid arguments",
                "isError": True,
                "shouldContinue": True
            }


# ============================================
# Usage Example
# ============================================

if __name__ == "__main__":
    print("🔧 Agent-Native Search MCP Server\n")

    server = SearchMCPServer()

    # Example 1: List supported countries
    print("1️⃣ Listing supported countries...")
    result = server.list_supported_countries()
    print(f"   {result['text']}")
    for country in result['countries']:
        print(f"   - {country['code']}: {country['name']}")

    # Example 2: Get config for Indonesia
    print("\n2️⃣ Getting Indonesia config...")
    result = server.get_config(country="ID")
    print(f"   {result['text']}")
    if result['success']:
        print(f"   Country name: {result['country_name']}")
        print(f"   Grades: {result['grades']}")

    # Example 3: Execute search
    print("\n3️⃣ Executing search...")
    result = server.search(
        country="ID",
        grade="1",
        subject="math"
    )
    print(f"   {result['text']}")
    if result['success']:
        print(f"   Top score: {result['search_metadata']['top_score']}")

    # Example 4: Get search history
    print("\n4️⃣ Getting search history...")
    result = server.get_search_history()
    print(f"   {result['text']}")

    # Example 5: Complete task
    print("\n5️⃣ Completing task...")
    result = server.complete_task(
        summary="Demonstrated all atomic tools",
        status="success"
    )
    print(f"   ✅ {result['summary']}")
    print(f"   shouldContinue: {result['shouldContinue']}")
