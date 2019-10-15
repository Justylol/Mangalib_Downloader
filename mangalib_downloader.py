import asyncio
from aiohttp import ClientSession
from aiohttp.client_exceptions import (ClientResponseError, ServerDisconnectedError, ServerTimeoutError,
                                       ClientConnectorError)
import aiofiles
import os
import random
import requests
from bs4 import BeautifulSoup
from math import ceil
import sys


async def save_image(data, filename):
    async with aiofiles.open(filename, 'wb') as file:
        await file.write(data)


async def get_image(url):
    while True:

        try:
            async with ClientSession(headers={"Connection": "close"}) as session:
                response = await session.get(url, allow_redirects=True, ssl=False)
                response.raise_for_status()
                return await response.read()

        except (
                ClientResponseError, ServerDisconnectedError, ServerTimeoutError, ClientConnectorError,
                asyncio.TimeoutError
        ):
            delay = random.randint(1, 5)
            await asyncio.sleep(delay)


async def get_chapter_info(chapter_id):
    chapter_info_url = f'https://mangalib.me/download/{chapter_id}'

    while True:

        try:
            async with ClientSession(headers={"Connection": "close"}) as session:
                response = await session.get(chapter_info_url, allow_redirects=True, ssl=False)
                response.raise_for_status()
                return await response.json()

        except (
                ClientResponseError, ServerDisconnectedError, ServerTimeoutError, ClientConnectorError,
                asyncio.TimeoutError
        ):
            delay = random.randint(1, 5)
            await asyncio.sleep(delay)


async def get_chapter(chapter_id, manga_name):
    chapter_info = await get_chapter_info(chapter_id)
    chapter_slug = chapter_info["chapter"]["slug"]
    chapter_name = chapter_info["chapter"]["number"]
    folder_name = f'{manga_name}/{chapter_name}'
    os.makedirs(folder_name, exist_ok=True)  # no way to async create folder :(
    img_count = 1

    print(f'Chapter {chapter_name} download: Start')

    for image in chapter_info['images']:
        img_url = f'https://img2.mangalib.me/manga/{manga_name}/chapters/{chapter_slug}/{image}'

        data = await get_image(img_url)

        filename = f'{folder_name}/{img_count}.png'

        await save_image(data, filename)

        img_count += 1

    print(f'Chapter {chapter_name} download: Done')


async def main(url):
    tasks = list()
    portion = 10  # optimal portion value to download from mangalib and not getting to much of errors
    # Get manga data
    manga_page_response = requests.get(url)
    manga_name = manga_page_response.request.path_url.replace('/', '')
    # Collect chapters ids for download
    soup = BeautifulSoup(manga_page_response.text, features="html.parser")
    items = soup.find_all("div", 'chapter-item')

    chapters_ids = [item.attrs['data-id'] for item in items]

    portion_count = ceil(len(chapters_ids) / portion)

    for i in range(portion_count):
        from_index = portion * i
        to_index = portion * (i + 1)

        for chapter_id in chapters_ids[from_index:to_index]:
            task = asyncio.create_task(get_chapter(chapter_id, manga_name))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    manga_url = sys.argv[1]
    asyncio.run(main(manga_url))
