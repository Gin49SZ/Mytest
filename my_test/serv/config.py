from aiohttp import web
from pathlib import Path


home_path = Path(__file__).parent.parent
web_routes = web.RouteTableDef()
