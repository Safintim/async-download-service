import os.path
import logging
import asyncio
import aiofiles
from aiohttp import web

import tools


zip_cmd = ['zip', '-', '-r']
logger = logging.getLogger(__name__)


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

    zip_cmd.append(path)
    zip_proc = await asyncio.create_subprocess_exec(
        *zip_cmd,
        stdout=asyncio.subprocess.PIPE
    )

    try:
        while True:
            archive_chunc = await zip_proc.stdout.readline()
            if not archive_chunc:
                break
            await response.write(archive_chunc)

            logger.info('Sending archive chunk ...')
            await asyncio.sleep(int(config['RESPONSE_DELAY']))
    except (asyncio.CancelledError, ConnectionResetError):
        logger.info('Download was interrupted')
        raise
    finally:
        zip_proc.kill()
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
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    app['config'] = tools.setup_config(namespace.__dict__)

    formatter = logging.Formatter('%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.setLevel(level=logging.WARN)
    logger.addHandler(handler)
    if app['config']['LOGGING']:
        logger.setLevel(level=logging.DEBUG)

    web.run_app(app)
