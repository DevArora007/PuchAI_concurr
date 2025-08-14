import os
import httpx
from fastmcp import FastMCP
from mcp.types import TextContent, INTERNAL_ERROR, ErrorData
from mcp import McpError
from dotenv import load_dotenv

# Load env vars
load_dotenv()
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "YOUR_KEY_HERE")

class CurrencyConverter:
    BASE = "https://v6.exchangerate-api.com/v6"

    @classmethod
    async def convert(cls, frm: str, to: str, amount: float | None = None) -> dict:
        """Fetch conversion data from ExchangeRate API."""
        if amount is not None:
            url = f"{cls.BASE}/{EXCHANGE_API_KEY}/pair/{frm.upper()}/{to.upper()}/{amount}"
        else:
            url = f"{cls.BASE}/{EXCHANGE_API_KEY}/pair/{frm.upper()}/{to.upper()}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url)
            except httpx.HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Network error: {e!r}"))

        if resp.status_code != 200:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"ExchangeRate API returned status {resp.status_code}"))

        data = resp.json()
        if data.get("result") != "success":
            error_info = data.get("error-type", "Unknown error")
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"ExchangeRate API error: {error_info}"))

        return data


# Create MCP server
mcp = FastMCP("Currency Converter MCP Server")

@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> TextContent:
    """
    Convert an amount from one currency to another.
    Example: convert_currency(100, "USD", "INR")
    """
    data = await CurrencyConverter.convert(from_currency, to_currency, amount)
    converted_amount = data.get("conversion_result")
    rate = data.get("conversion_rate")

    return TextContent(
        type="text",
        text=f"{amount} {from_currency.upper()} = {converted_amount} {to_currency.upper()} (Rate: {rate})"
    )


if __name__ == "__main__":
    import asyncio
    async def main():
        print("🚀 Starting Currency Converter MCP server on http://0.0.0.0:8086")
        await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)
    asyncio.run(main())
