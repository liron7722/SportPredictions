#!/usr/bin/env python3

class Error(Exception):
    """Base class for other exceptions"""
    pass


class PageNotLoaded(Error):
    """Exception raised for errors with status code of request.

        Attributes:
            url -- url of the request
            status_code -- status code of request
            message -- explanation of the error
        """

    def __init__(self, url, status_code, message=f"Got bad status code when trying to get the link provided"):
        self.url = url
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'Url: {self.url}\n' \
               f'Status Code: {self.status_code}\n' \
               f'Message: {self.message}\n' \
               f'Please try again later...\n' \
               f'Mean while you can check manually if the site is down or ip address is blocked.'


class ParseError(Error):
    """Exception raised for errors with status code of request.

        Attributes:
            url -- url of the request
            func -- function name where error accord
            message -- explanation of the error
        """

    def __init__(self, url, message=f"Got error when trying to parse the data provided"):
        self.url = url
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'Url: {self.url}\n' \
               f'Message: {self.message}'
