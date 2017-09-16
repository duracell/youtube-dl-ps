# coding: utf-8

from __future__ import unicode_literals

from .once import OnceIE
from ..compat import (
    compat_urllib_parse_unquote,
)
from ..utils import (
    unescapeHTML,
    js_to_json,
    int_or_none,
)


class PietsmietIE(OnceIE):
    _VALID_URL = r'https?://(?:www\.)?pietsmiet\.de/gallery/categories/[\w-]+/(?P<id>\d+)-.*/?'
    _TEST = {
        'url': 'http://www.pietsmiet.de/gallery/categories/8-frag-pietsmiet/29844-fps-912',
        'info_dict': {
            'id': '29844',
            'ext': 'mp4',
            'title': 'Was würdet ihr die Maus fragen? 🎮 Frag PietSmiet #912',
        },
        'params': {
            'skip_download': True,  # m3u8 downloads
        },
    }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        data_video_config = self._search_regex(
            r'var config=(.*?);var', webpage, 'video config')
        data_video = self._parse_json(js_to_json(unescapeHTML(data_video_config)), page_id)

        formats = []

        m3u8_manifest_url = data_video['sources'][0]['file']
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_manifest_url, page_id, 'mp4', 'm3u8_native',
            m3u8_id='hls')

        # Give reproducible names for HLS formats instead of hls-<bitrate>
        for f in m3u8_formats:
            f['format_id'] = 'hls-{}p'.format(f['height'])

        formats.extend(m3u8_formats)

        if len(data_video['sources']) > 1:
            http_video = data_video['sources'][1]

            # Calculate resolution for HTTP format but should always be 1280x720
            format_height_raw = self._search_regex(
                '([0-9]+)p', http_video['label'], 'http video height',
                default=720, fatal=False)
            format_height = int_or_none(format_height_raw)

            if format_height:
                format_width = float(format_height) * (16 / 9)

                formats.append({
                    'url': "https:{}".format(http_video['file']),
                    'ext': http_video['type'],
                    'format_id': 'http-{}'.format(http_video['label']),
                    'width': int_or_none(format_width),
                    'height': format_height,
                    'fps': 30.0,
                })

        self._sort_formats(formats)

        return {
            'id': page_id,
            'display_id': page_id,
            'title': compat_urllib_parse_unquote(data_video['abouttext']),
            'formats': formats,
            'thumbnail': 'http://www.pietsmiet.de/{}'.format(data_video.get('image')),
        }
