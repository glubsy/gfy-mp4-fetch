import requests
import constants

class GfycatClient(object):
    """credits to https://github.com/ankeshanand/py-gfycat/"""

    def __init__(self):
        pass

    def query_gfy(self, gfyname):
        """Query a gfy name for URLs and more information."""
        request_session = requests.Session()
        request_session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; \
rv:55.0) Gecko/20100101 Firefox/54.0'})
        req = request_session.get(constants.QUERY_ENDPOINT + gfyname)
        if req.status_code != 200:
            raise GfycatClientError('Unable to query gfycay for the file',
                                    req.status_code)

        return req.json()


class GfycatClientError(Exception):
    """credits to https://github.com/ankeshanand/py-gfycat/"""

    def __init__(self, error_message, status_code=None):
        self.status_code = status_code
        self.error_message = error_message

    def __str__(self):
        if self.status_code:
            return "(%s) %s" % (self.status_code, self.error_message)

        return self.error_message