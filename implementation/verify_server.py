import os
import sys

import asyncio

# Add current directory to path so we can import mcp_server
sys.path.append(os.path.dirname(__file__))

async def verify():
    print("Verifying MCP Server discovery...")
    try:
        from mcp_server import mcp
        
        # Verify tools
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        print(f"Discovered tools: {tool_names}")
        
        required_tools = ["search", "insert", "aggregate"]
        for tool in required_tools:
            if tool in tool_names:
                print(f"  [OK] Tool '{tool}' found.")
            else:
                print(f"  [FAIL] Tool '{tool}' NOT found.")
                return False
        
        # Verify resources
        resources = await mcp.list_resources()
        resource_uris = [str(r.uri) for r in resources]
        print(f"Discovered resources: {resource_uris}")
        
        if "schema://database" in resource_uris:
            print("  [OK] Resource 'schema://database' found.")
        else:
            print("  [FAIL] Resource 'schema://database' NOT found.")
            return False
            
        # Resource templates
        templates = await mcp.list_resource_templates()
        template_uris = [str(t.uri_template) for t in templates]
        print(f"Discovered resource templates: {template_uris}")
        
        if "schema://table/{table_name}" in template_uris:
            print("  [OK] Resource template 'schema://table/{table_name}' found.")
        else:
            print("  [FAIL] Resource template 'schema://table/{table_name}' NOT found.")
            return False
            
        print("\nAll discovery checks passed!")
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if asyncio.run(verify()):
        sys.exit(0)
    else:
        sys.exit(1)
