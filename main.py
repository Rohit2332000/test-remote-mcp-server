from fastmcp import FastMCP
import random 
import json

#Create the fast mcp server instance

mcp=FastMCP("Simple Calculator Server")

#Tool:Add two numbers

@mcp.tool
def add(a:int ,b:int)->int:
    """Add two numbers together
    Args:
        a:First number
        b:Second number
    Returns:
        The sum of a and b
        """
        
    return a +b

#Tool:Generate a random number
@mcp.tool
def random_number(min_value:int =1,max_val:int=100)->int:
    """Generate a random number between a given range.
    
    Args:
        min_value:Minumum value(default:1)
        max_value:Maximum value(default:100)
        
    Returns:
        A random integer between min_value and max_value
    """    
    return random.randint(min_value,max_val)

#Resource:Server Information

@mcp.resource("info://server")
def server_info()->str:
    """Get information about this server"""
    info={
        "name":"Simple calculator server",
        "version":"1.0.0",
        "description":"A basic MCP server with math tools",
        "tools":["add","random number"],
        "author":"Rohit"
    }
    return json.dumps(info,indent=2)

#Start the server

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )

