import asyncio
import logging

from .soup import make_page

log = logging.getLogger(__name__)

@asyncio.coroutine
def get_page(client, url):
    log.debug('Fethching {!r}'.format(url))
    response = yield from client.get(url)
    if response.status == 200:
        return (yield from response.read())
    else:
        # FIXME: in production code this would handle redirects and raise
        # suitable exceptions:
        raise ValueError('Got {} whilst fetching {!r}'.format(
            response.status, url))


@asyncio.coroutine
def _crawl(client, url, pages, loop):
    html_string = yield from get_page(client, url)
    page = make_page(url, html_string)
    internal_urls = page.internal_urls - page.resource_urls
    new_internal_urls = filter(lambda u: u not in pages, internal_urls)
    tasks = []
    for new_url in new_internal_urls:
        task = loop.create_task(_crawl(client, new_url, pages, loop=loop))
        pages[new_url] = task
        tasks.append(task)
    for linked_page in (yield from asyncio.gather(*tasks, loop=loop)):
        pages[linked_page.url] = linked_page
    return page


@asyncio.coroutine
def crawl(client, url, loop):
    pages = {}
    yield from _crawl(client, url, pages, loop)
    return pages
