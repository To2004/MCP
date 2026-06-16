"""MCP asset scanner — enumerate and rank the assets each connected MCP exposes.

An MCP server is connected to an *asset store* whose unit depends on the server
kind (files for filesystem, tables for sqlite, channels for slack, ...). The
scanner connects to each configured server, enumerates the assets it can reach
(read-only), and ranks them into a ``Rank | Name | Risk Level | Reasoning``
table using the shared sensitivity anchors plus the local LLM.
"""

from .config_reader import ConnectionSpec, read_configured_servers
from .enumerator import AssetGroup, AssetInventory, enumerate_assets
from .ranker import RankedAsset, rank_inventory

__all__ = [
    "ConnectionSpec",
    "read_configured_servers",
    "AssetGroup",
    "AssetInventory",
    "enumerate_assets",
    "RankedAsset",
    "rank_inventory",
]
