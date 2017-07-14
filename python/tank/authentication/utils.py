# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import urlparse


def cleanup_url(server_url):

    # First clean up any extra spaces.
    server_url = server_url.strip()

    # Then break up the url into chunks
    parsed_url = urlparse.urlparse(server_url)

    # The given url https://192.168.1.250:30/path?a=b is parsed such that
    # scheme => https
    # netloc => 192.168.1.250:30
    # path = /path
    # query = a=b

    # As such, when sanitizing a url, we want to keep only the scheme and
    # network location

    # Then extract the good parts from the url
    clean_url = urlparse.ParseResult()
    clean_url.scheme = parsed_url.scheme or "https"
    clean_url.netloc = parsed_url.netloc

    return urlparse.unparseurl(clean_url)
