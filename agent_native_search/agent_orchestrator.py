"""
Agent-Native Search Orchestrator

Demonstrates how an agent autonomously decides search strategy
using atomic tools - following agent-native architecture principles.

Key principle: Agent decides WHAT to do, tools provide CAPABILITIES.
No hardcoded workflows - behavior emerges from system prompt + tools.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_native_search.mcp_search_server import SearchMCPServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchAgentOrchestrator:
    """
    Agent orchestrator for educational resource search.

    This orchestrator follows agent-native principles:
    - Provides atomic tools (not workflows)
    - Agent decides strategy via system prompt
    - Explicit completion signal
    - Iterative refinement based on results
    """

    def __init__(self):
        self.mcp_server = SearchMCPServer()
        self.max_iterations = 10
        self.conversation_history: List[Dict] = []

    def process_request(self, user_message: str) -> Dict:
        """
        Process a user search request.

        The agent will:
        1. Understand the request
        2. Check configuration
        3. Decide search strategy
        4. Execute searches iteratively
        5. Complete when goal is achieved

        Args:
            user_message: User's natural language request

        Returns:
            Final result with summary
        """
        logger.info(f"Processing user request: {user_message}")

        # Initialize conversation
        self.conversation_history = [
            {"role": "system", "content": self._load_system_prompt()},
            {"role": "user", "content": user_message}
        ]

        # Agent loop - continues until complete_task is called
        iteration = 0
        result = None

        while iteration < self.max_iterations:
            logger.info(f"--- Iteration {iteration + 1} ---")

            # Get agent response (in real implementation, this would call an LLM)
            # For this demo, we simulate agent decision-making
            agent_action = self._simulate_agent_decision(user_message, iteration)

            # Execute the action
            result = self._execute_action(agent_action)

            # Check for completion signal
            if result.get('isComplete'):
                logger.info("✅ Task completed")
                break

            # Check if should continue
            if not result.get('shouldContinue', True):
                logger.info("⏹️ Agent signaled to stop")
                break

            iteration += 1

        if iteration >= self.max_iterations:
            logger.warning("⚠️ Max iterations reached")

        return result or {
            "status": "no_result",
            "message": "Agent completed without returning a result"
        }

    def _load_system_prompt(self) -> str:
        """Load the agent's system prompt"""
        prompt_path = Path(__file__).parent / "agent_system_prompt.md"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return "You are a helpful educational resource search assistant."

    def _simulate_agent_decision(self, user_message: str, iteration: int) -> Dict:
        """
        Simulate agent decision-making.

        In a real implementation, this would call an LLM (Claude, GPT, etc.)
        with the conversation history and available tools.

        For this demo, we use rule-based simulation to show the pattern.
        """
        logger.info("🤖 Agent deciding next action...")

        # Parse user request (simplified)
        request_lower = user_message.lower()

        # Extract parameters
        country = self._extract_country(request_lower)
        grade = self._extract_grade(request_lower)
        subject = self._extract_subject(request_lower)

        # Decision logic based on iteration
        if iteration == 0:
            # First iteration: Check configuration
            logger.info("📋 Decision: Check configuration first")
            return {
                "tool": "get_config",
                "arguments": {"country": country}
            }

        elif iteration == 1:
            # Second iteration: Execute search
            logger.info("🔍 Decision: Execute search")
            return {
                "tool": "search",
                "arguments": {
                    "country": country,
                    "grade": grade,
                    "subject": subject
                }
            }

        elif iteration == 2:
            # Third iteration: Store successful result and complete
            logger.info("💾 Decision: Store result and complete")
            return {
                "tool": "complete_task",
                "arguments": {
                    "summary": f"Found educational resources for {country} Grade {grade} {subject}",
                    "status": "success"
                }
            }

        else:
            # Fallback: Complete task
            logger.info("✅ Decision: Complete task")
            return {
                "tool": "complete_task",
                "arguments": {
                    "summary": "Search completed",
                    "status": "success"
                }
            }

    def _execute_action(self, action: Dict) -> Dict:
        """Execute an agent action using MCP tools"""
        tool_name = action.get("tool")
        arguments = action.get("arguments", {})

        logger.info(f"🔧 Executing: {tool_name}({arguments})")

        result = self.mcp_server.call_tool(tool_name, arguments)

        # Log result
        if result.get('success'):
            logger.info(f"✅ {result.get('text', 'Success')}")
        else:
            logger.warning(f"❌ {result.get('text', 'Failed')}")

        return result

    def _extract_country(self, text: str) -> str:
        """Extract country from user request"""
        country_map = {
            "indonesia": "ID",
            "indonesian": "ID",
            "saudi": "SA",
            "saudi arabia": "SA",
            "china": "CN",
            "chinese": "CN",
            "us": "US",
            "usa": "US",
            "america": "US",
            "united states": "US"
        }

        text_lower = text.lower()
        for key, code in country_map.items():
            if key in text_lower:
                return code

        return "ID"  # Default to Indonesia

    def _extract_grade(self, text: str) -> str:
        """Extract grade from user request"""
        import re

        # Look for "grade X", "grade x", "kelas x", etc.
        patterns = [
            r'grade\s*(\d+)',
            r'kelas\s*(\d+)',
            r'year\s*(\d+)',
            r'年级\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)

        return "1"  # Default to Grade 1

    def _extract_subject(self, text: str) -> str:
        """Extract subject from user request"""
        subject_map = {
            "math": "math",
            "mathematics": "math",
            "matematika": "math",
            "数学": "math",
            "science": "science",
            "sciences": "science",
            "ipa": "science",
            "物理": "science",
            "english": "english",
            "语言": "english"
        }

        text_lower = text.lower()
        for key, code in subject_map.items():
            if key in text_lower:
                return code

        return "math"  # Default to math


# ============================================
# Example Usage
# ============================================

def demo_search_requests():
    """Demonstrate agent handling various search requests"""

    print("\n" + "=" * 60)
    print("🤖 Agent-Native Search Orchestrator Demo")
    print("=" * 60 + "\n")

    orchestrator = SearchAgentOrchestrator()

    # Demo requests
    requests = [
        "Find math resources for Grade 1 in Indonesia",
        "I need science materials for Grade 3 in Indonesia",
        "Show me what countries are supported"
    ]

    for i, request in enumerate(requests, 1):
        print(f"\n{'─' * 60}")
        print(f"👤 User Request {i}: {request}")
        print(f"{'─' * 60}\n")

        result = orchestrator.process_request(request)

        print(f"\n🤖 Agent Response:")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Summary: {result.get('summary', result.get('text', 'N/A'))}")

        if result.get('status') == 'success':
            print(f"   ✅ Task completed successfully")
        else:
            print(f"   ⚠️  Task completed with notes")

    print(f"\n{'=' * 60}")
    print("✅ Demo completed")
    print(f"{'=' * 60}\n")


def demo_interactive():
    """Interactive demo where user can type requests"""
    print("\n" + "=" * 60)
    print("🤖 Agent-Native Search - Interactive Mode")
    print("=" * 60)
    print("Type 'exit' to quit\n")

    orchestrator = SearchAgentOrchestrator()

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n🤖 Agent: ", end="", flush=True)
            result = orchestrator.process_request(user_input)

            print(f"\n   {result.get('summary', result.get('text', 'Done'))}")

            if result.get('results'):
                print(f"\n   Found {len(result['results'])} results:")
                for j, r in enumerate(result['results'][:3], 1):
                    print(f"   {j}. {r.get('title', 'N/A')} ({r.get('score', 0):.1f}/10)")

            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        demo_interactive()
    else:
        demo_search_requests()
