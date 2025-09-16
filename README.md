# Monumenten MCP Server 🏛️

A Model Context Protocol (MCP) server that enables AI assistants to check monumental status of Dutch addresses. Connects to the Dutch BAG (Basisadministratie Adressen en Gebouwen) data and Ministry of Cultural Heritage (Rijksdienst voor het Cultureel Erfgoed) to identify national monuments, protected cityscapes, and municipal monuments.

> [!NOTE]
> This MCP server is based on the [monumenten](https://github.com/woonstadrotterdam/monumenten) package. For more information, see the [monumenten](https://github.com/woonstadrotterdam/monumenten) package.

## What This Does

This MCP server allows AI assistants to:

- 🏠 **Find verblijfsobject IDs** - Convert Dutch addresses to BAG identifiers (`verblijfsobject_id`)
- 🏛️ **Check monumental status** - Determine if a property is protected as cultural heritage
- 📍 **Support flexible address input** - Search by postal code + house number or full address
- 🔍 **Handle address variations** - Support house letters and suffixes (30A, 30-2, etc.)

### Available Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| **`get_verblijfsobject_id`** | `house_number`, `postal_code` OR `street` + `house_number` + `city`, optional `house_letter`, `house_suffix` | Finds BAG verblijfsobject ID for an address |
| **`get_monumental_status`** | `bag_verblijfsobject_id` | Checks if a property is a rijksmonument, in protected cityscape, or municipal monument |

## Quick Setup

Add to your AI assistant's MCP configuration:

```json
{
  "mcpServers": {
    "monumenten": {
      "command": "uvx",
      "args": ["mcp-monumenten"]
    }
  }
}
```

For local development:

```json
{
  "mcpServers": {
    "monumenten": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/mcp-monumenten", "mcp-monumenten"]
    }
  }
}
```

## Usage Examples

### Finding Monumental Status

**"What is the monumental status of Coolsingel 30, Rotterdam?"**

The AI will:
1. Convert the address to a BAG verblijfsobject ID
2. Check monument registries
3. Report rijksmonument status, protected cityscape inclusion, or municipal monument designation

**"Is 1234AB 30-2 a rijksmonument?"**

The AI can handle:
- Postal code + house number format
- House number suffixes (30-2, 30A, etc.)
- Direct verblijfsobject ID lookups

### Address Flexibility

The server handles Dutch address formats:
- `1234AB 30` - Basic postal code + house number
- `1234AB 30-2` - With house number suffix
- `1234AB 30A` - With house letter
- `Coolsingel 30, Rotterdam` - Full street address

## Installation

### Via uvx (Recommended)

```bash
uvx mcp-monumenten
```

### Local Development

```bash
git clone https://github.com/woonstadrotterdam/mcp-monumenten.git
cd mcp-monumenten
uv sync
uv run --project . mcp-monumenten
```

## Data Sources

- **[Kadaster - BAG (Basisadministratie Adressen en Gebouwen)](https://www.kadaster.nl/)** - Official Dutch address registry
- **[RCE (Rijksdienst voor het Cultureel Erfgoed)](https://www.rijksoverheid.nl/ministeries/cultureel-erfgoed/rijksdienst-voor-het-cultureel-erfgoed)** - National monuments registry

## License

MIT License - see [LICENSE](LICENSE) file for details.