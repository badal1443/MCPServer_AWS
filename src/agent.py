import asyncio
import json
import os
from dotenv import load_dotenv

from mcp import ClientSession
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from google import genai
from google.genai import types

load_dotenv()

LAMBDA_URL = os.getenv("LAMBDA_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def clean_schema(schema):
    if not isinstance(schema, dict):
        return schema
    # Gemini 2.0 is strict; it dislikes these keys in the tool declaration
    return {k: v for k, v in schema.items() if k not in ["$schema", "additionalProperties"]}

async def run_agent():
    # Correct 2026 AWS Transport
    transport = aws_iam_streamablehttp_client(
        endpoint=LAMBDA_URL,
        aws_region=AWS_REGION,
        aws_service="lambda"
    )

    print(f"Connecting to MCP Server at {LAMBDA_URL}...")
    
    # Note: Using the (read, write, _) 3-value unpacking for HTTP
    async with transport as (read, write, get_session_id):
        async with ClientSession(read, write) as mcp_session:
            try:
                # 1. Increase timeout for Lambda cold starts
                # 2. Use a specific timeout to distinguish between 'hang' and 'error'
                await asyncio.wait_for(mcp_session.initialize(), timeout=60)
                
                # Verify we actually got a session ID from the Lambda
                session_id = get_session_id()
                if not session_id:
                    print("⚠️ Warning: No mcp-session-id received. Lambda might be stateless.")
                else:
                    print(f"✅ Connected! Session ID: {session_id}")
            except asyncio.TimeoutError:
                print("❌ Error: Lambda took too long to respond (Cold Start timeout).")
                return
            except Exception as e:
                print(f"❌ Initialization failed: {e}")
                # This is where 'Session terminated' is caught
                return
            mcp_tools = await mcp_session.list_tools()

            # Mapping MCP tools to Gemini Function Declarations
            gemini_tools = [types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=clean_schema(tool.inputSchema)
                ) for tool in mcp_tools.tools
            ])]

            print(f"key:::: {os.getenv("GEMINI_API_KEY")}")

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            messages = []

            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]: break
                
                messages.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

                # Loop to handle multiple tool calls in one turn (multi-turn reasoning)
                while True:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-lite", 
                        contents=messages,
                        config=types.GenerateContentConfig(tools=gemini_tools)
                    )

                    # Add Gemini's thought/tool call to history
                    messages.append(response.candidates[0].content)
                    
                    # Check if Gemini wants to call a tool
                    tool_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]

                    if not tool_calls:
                        # If no more tools, print the final textual response
                        if response.text:
                            print(f"Agent: {response.text}")
                        break

                    # Execute all requested tools
                    for fc in tool_calls:
                        print(f"--- [Action] Executing: {fc.name} ---")
                        # MCP tool call
                        result = await mcp_session.call_tool(fc.name, fc.args)
                        
                        # MCP content is usually a list; we want the text content
                        raw_text = result.content[0].text if result.content else "{}"
                        
                        # Tool responses to Gemini should ideally be dicts
                        try:
                            parsed_response = json.loads(raw_text)
                        except:
                            parsed_response = {"output": raw_text}

                        # Append the result to the conversation
                        messages.append(types.Content(
                            role="tool", 
                            parts=[types.Part.from_function_response(
                                name=fc.name, 
                                response=parsed_response
                            )]
                        ))
                    
                    # The loop continues to call generate_content again with the tool results

if __name__ == "__main__":
    asyncio.run(run_agent())