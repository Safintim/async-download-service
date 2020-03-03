import os.path
import logging
import asyncio
import aiofiles
from aiohttp import web

import tools


TEMPLATE_COMMAND = 'zip - -r {}'


logging.basicConfig(
    format='%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO)


async def archivate(request):
    config = request.app['config']
    path = '{}/{}'.format(config['FILES_DIR'], request.match_info['archive_hash'])

    if not os.path.exists(path):
        raise web.HTTPNotFound(text='Архив не существует или был удален')

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(config['ARCHIVE_NAME'])

    await response.prepare(request)
    response.enable_chunked_encoding()

    proc = await asyncio.create_subprocess_shell(
        TEMPLATE_COMMAND.format(path),
        stdout=asyncio.subprocess.PIPE
    )

    try:
        while True:
            archive_chunc = await proc.stdout.readline()
            if not archive_chunc:
                break

            await response.write(archive_chunc)

            if config['LOGGING']:
                logging.info('Sending archive chunk ...')

            await asyncio.sleep(int(config['RESPONSE_DELAY']))
    except (asyncio.CancelledError, ConnectionResetError):
        if config['LOGGING']:
            logging.info('Download was interrupted')
        proc.kill()
        raise
    finally:
        response.force_close()

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = tools.create_parser()
    namespace = parser.parse_args()

    app = web.Application()
    app['config'] = tools.setup_config(namespace.__dict__)
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
