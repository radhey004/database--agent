import asyncio
from mcp import Client


async def main():

    async with Client(
        "http://127.0.0.1:9000/mcp"
    ) as client:

        print("Connected!")

        result = await client.call_tool(
            "run_sql",
            {
                "query": "SELECT COUNT(*) AS count FROM users"
            }
        )

        print("Tool returned!")
        print(result)

        print("Content:")
        print(result.content[0].text)


asyncio.run(main())