from aiohttp import web


from serv.config import web_routes, home_path
import serv.dblock
import serv.cookie
import serv.student
import serv.teacher


app = web.Application()
app.add_routes(web_routes)
app.add_routes([web.static("/", home_path / "static")])
serv.dblock.setup(app, dsn="host=localhost dbname=examdb user=examdb")

if __name__ == "__main__":
    web.run_app(app, port=8080)
