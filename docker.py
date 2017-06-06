#!/usr/bin/env python3.6
"""
pydf pdf generation

To generate PDF POST (or GET with data if possible) you HTML data to /generate.pdf

For example:

    docker run -p 8000:80 -d samuelcolvin/pydf
    curl -d '<h1>this is html</h1>' http://localhost:8000/generate.pdf > created.pdf
    open "created.pdf"
"""

import os
from aiohttp import web
from pydf import AsyncPydf


async def startup(app):
    app['apydf'] = AsyncPydf(loop=app.loop)


async def index(request):
    return web.Response(text=__doc__)


async def generate(request):
    data = await request.read()
    pdf_content = await app['apydf'].generate_pdf(data.decode())
    return web.Response(body=pdf_content, content_type='application/pdf')

app = web.Application()
app.on_startup.append(startup)
app.router.add_get('/', index)
app.router.add_route('*', '/generate.pdf', generate)
port = int(os.getenv('PORT', '80'))
print(f'starting pydf server on port {port}', flush=True)
web.run_app(app, port=port, print=lambda v: None)