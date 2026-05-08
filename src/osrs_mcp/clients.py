from osrs_mcp.prices import PricesClient
from osrs_mcp.runelite import RuneLiteSyncClient
from osrs_mcp.wiki import WikiClient
from osrs_mcp.wiseoldman import WiseOldManClient

wom = WiseOldManClient.build()
runelite = RuneLiteSyncClient.build()
wiki = WikiClient.build()
prices = PricesClient.build()
