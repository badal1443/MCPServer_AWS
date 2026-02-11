import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client  # Use the SSE client
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Helper to remove fields Gemini doesn't support
def clean_schema(schema):
    if not isinstance(schema, dict):
        return schema
    # Gemini doesn't like '$schema' or 'additionalProperties' in tool definitions
    return {k: v for k, v in schema.items() if k not in ["$schema", "additionalProperties"]}

async def run_agent():
    # Connect to the ALREADY RUNNING server via its URL
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            mcp_tools = await mcp_session.list_tools()

            # 2. Map MCP tools to Gemini format
            gemini_tools = [types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=clean_schema(tool.inputSchema)
                ) for tool in mcp_tools.tools
            ])]

            # Persistent history to keep context across different questions
            messages = []

            gemini_api_key=os.getenv("GEMINI_API_KEY")

            client = genai.Client(api_key=gemini_api_key)

            while True: # OUTER LOOP: For user interaction
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                # Add user question to history
                messages.append(types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text=user_input)]
                ))

                # 3. Maintain conversation history for the "Loop"
                #messages = [types.Content(role="user", parts=[types.Part.from_text(text="Transition Jira ticket with ticket ID REL-1 status to In Progress")])]
                # The agent now uses the tools hosted at localhost:8000
                while True:
                    # Send the request to Gemini
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite", # Or gemini-2.5-flash-lite
                        contents=messages,
                        config=types.GenerateContentConfig(tools=gemini_tools)
                    )

                    # Add the AI's response (which might be a tool call) to history
                    messages.append(response.candidates[0].content)

                    # 4. Check if Gemini wants to use a tool
                    # (Look for parts that have a function_call)
                    tool_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]

                    if not tool_calls:
                        # If no more tool calls, print the final answer and exit
                        print(f"Agent Response: {response.text}")
                        break

                    # 5. Execute the Tool Call on the MCP Server
                    for fc in tool_calls:
                        print(f"--- Calling MCP Tool: {fc.name} ---")
                        
                        # Forward the arguments to your actual Jira/MCP code
                        result = await mcp_session.call_tool(fc.name, fc.args)

                        # 1. Extract the text content
                        raw_text = result.content[0].text if result.content else "{}"
                        
                        try:
                            # 2. Convert the string back into a Python dictionary
                            parsed_response = json.loads(raw_text)
                        except json.JSONDecodeError:
                            # Fallback if the tool returned plain text instead of JSON
                            parsed_response = {"output": raw_text}
                        

                        # Add the result back to the conversation
                        messages.append(types.Content(
                            role="tool", 
                            parts=[types.Part.from_function_response(
                                name=fc.name,
                                response=parsed_response
                            )]
                        ))

if __name__ == "__main__":
    asyncio.run(run_agent())