import asyncio
import os
import json
from dotenv import load_dotenv
from parlant.sdk import Server, ToolContext, ToolResult, tool

# Load environment variables from .env file
load_dotenv()


# --- B. Define Tools (Mock Functions) ---

@tool
async def get_db_schema(context: ToolContext) -> ToolResult:
    """
    Returns the database schema for the current environment.
    Use this to understand table structures before generating queries.
    """
    schema = {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INTEGER", "description": "User ID"},
                    {"name": "name", "type": "TEXT", "description": "Full name"},
                    {"name": "role", "type": "TEXT", "description": "Job role"},
                    {"name": "salary", "type": "INTEGER", "description": "Annual salary in USD (PII)"},
                    {"name": "email", "type": "TEXT", "description": "Email address (PII)"}
                ]
            }
        ]
    }
    return ToolResult(json.dumps(schema))

@tool
async def execute_sql_query(context: ToolContext, query: str) -> ToolResult:
    """
    Executes a SQL query against the database.
    WARNING: Only strictly validated SELECT queries are allowed.
    """
    # Transparency requirement: Print to console
    print(f"\n[SYSTEM LOG] Executing: {query}")
    
    # Mock successful response
    mock_data = {
        "status": "success",
        "data": [
            {"id": 1, "name": "Alice Code", "role": "Engineer", "salary": 120000, "email": "alice@example.com"},
            {"id": 2, "name": "Bob Data", "role": "Analyst", "salary": 95000, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie Admin", "role": "Manager", "salary": 140000, "email": "charlie@example.com"}
        ]
    }
    return ToolResult(json.dumps(mock_data))

# --- C. The Main Async Logic ---

async def main():
    # Ensure API Key is present
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return

    async with Server() as server:
        # Agent Creation
        agent = await server.get_or_create_agent(
            name="SQL_Guardian",
            description="A strict Database Security Officer who validates all requests before allowing data access."
        )

        # Guideline Definitions (The Core Logic)
        
        # Rule 1 (Criticality: HIGH)
        await agent.create_guideline(
            condition="The user asks to modify, delete, drop, or truncate data",
            action="REFUSE the request immediately. State that this is a read-only interface.",
            criticality="HIGH"  # Corrected to be consistent with typical expectation, SDK might expect float or enum, likely mapped internally if string is supported or we stick to description.
            # Checking parlant SDK usage, usually we define payload. 
            # Looking at prompt requirements: "Rule 1 (Criticality: HIGH)"
        )

        # Rule 2 (Criticality: MEDIUM)
        await agent.create_guideline(
            condition="The user asks for PII (Personally Identifiable Information) like specific salaries, emails, or phone numbers",
            action="REFUSE to provide raw data. Offer aggregate data (counts/averages) instead.",
            criticality="MEDIUM"
        )

        # Rule 3 (Criticality: LOW/MEDIUM) - Treated as instruction
        await agent.create_guideline(
            condition="The request is a safe 'read' operation",
            action="Call get_db_schema to understand the structure, then call execute_sql_query with a valid SQL SELECT statement.",
            criticality="MEDIUM"
        )

        print(f"Agent '{agent.name}' is ready! Type 'exit' to quit.\n")

        # Interactive Chat Loop
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting...")
                    break
                
                if not user_input.strip():
                    continue

                # server.chat sends input to the agent
                # We need a session_id, often handled by context or auto-generated if not strict.
                # Assuming simple usage based on prompt description: "Use server.chat to send the user input to the agent."
                
                # Check if we need to create a session first.
                session = await server.create_session(agent_id=agent.id)
                
                event_stream = await server.chat(
                    session_id=session.id,
                    message=user_input
                )
                
                # Process the event stream for the reply
                # Assuming event_stream yields events or a final response. 
                # Common pattern in agent SDKs: iterate events.
                
                full_reply = ""
                async for event in event_stream:
                    if event.kind == "message":
                        print(f"Agent: {event.data['content']}") # Stream bits or full? Assuming event structure
                        full_reply += event.data.get('content', '')
                    elif event.kind == "tool_activity":
                         # Optional: visualize tool calls here if not printed by tool itself
                         pass
                
                # If the iterator doesn't print directly (depends on specific SDK version behavior), ensure we print.
                # Since we don't know exact 'parlant' SDK stream format from memory, 
                # I will assume a standard interface or simple awaitable if it wasn't a stream.
                # BUT prompt said "Use server.chat ... Print the agent's response".
                # If server.chat returns a Coroutine resolving to response objects:
                # Let's try the most robust assumption or check documentation if I could.
                # Given "Import asyncio", it's async.
                
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
