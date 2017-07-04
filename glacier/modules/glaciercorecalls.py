#!/usr/bin/env python
# encoding: utf-8
"""
..  module:: botocorecalls
    :platform: Unix, Windows
    :synopsis: boto calls to access Amazon Glacier.

This depends on the boto library, use version 2.6.0 or newer.


    writer = GlacierWriter(glacierconn, GLACIER_VAULT)
    writer.write(block of data)
    writer.close()
    # Get the id of the newly created archive
    archive_id = writer.get_archive_id()from boto.connection
    import AWSAuthConnection
"""

# import modules

import urllib
import hashlib
import math
import json
import sys
import time
import boto.glacier.layer1

# import our modules
from modules import constants
from modules import glacierexception

# Placeholder, effectively renaming the class.
class GlacierConnection(boto.glacier.layer1.Layer1):

    pass

def chunk_hashes(data):
    """
    Break up the byte-string into 1MB chunks and return sha256 hashes
    for each.
    """
    chunk = constants.CHUNK_SIZE*constants.CHUNK_SIZE
    chunk_count = int(math.ceil(len(data)/float(chunk)))
    return [hashlib.sha256(data[i*chunk:(i+1)*chunk]).digest() for i in range(chunk_count)]

def tree_hash(fo):
    """
    Given a hash of each 1MB chunk (from chunk_hashes) this will hash
    together adjacent hashes until it ends up with one big one. So a
    tree of hashes.
    """
    hashes = []
    hashes.extend(fo)
    while len(hashes) > 1:
        new_hashes = []
        while True:
            if len(hashes) > 1:
                first = hashes.pop(0)
                second = hashes.pop(0)
                new_hashes.append(hashlib.sha256(first + second).digest())
            elif len(hashes) == 1:
                only = hashes.pop(0)
                new_hashes.append(only)
            else:
                break
        hashes.extend(new_hashes)
    return hashes[0]

def bytes_to_hex(str):
    return ''.join( [ "%02x" % ord( x ) for x in str] ).strip()

class GlacierWriter(object):
    """
    Presents a file-like object for writing to a Amazon Glacier
    Archive. The data is written using the multi-part upload API.
    """


    def __init__(self, connection, vault_name,
                 description=None,
                 part_size_in_bytes=constants.DEFAULT_PART_SIZE*1024*1024,
                 uploadid=None, logger=None):

        self.part_size = part_size_in_bytes
        self.vault_name = vault_name
        self.connection = connection
        self.logger = logger
        self.total_retries = 0

        if uploadid:
            self.uploadid = uploadid
        else:
            response = self.connection.initiate_multipart_upload(
                    self.vault_name,
                    self.part_size,
                    description)
            self.uploadid = response['UploadId']

        self.uploaded_size = 0
        self.tree_hashes = []
        self.closed = False

    def write(self, data):

        if self.closed:
            raise glacierexception.CommunicationError(
                "Tried to write to a GlacierWriter that is "\
                "already closed.",
                code='InternalError')

        len_data = len(data)
        if len_data > self.part_size:
            raise glacierexception.InputException (
                "Block of data provided({}) "\
                "must be equal "
                "to or smaller than the set "
                "block size({}).".format(len_data, self.part_size),
                code='InternalError')

        part_tree_hash = tree_hash(chunk_hashes(data))
        self.tree_hashes.append(part_tree_hash)
        headers = {
                   "x-amz-glacier-version": "2012-06-01",
                    "Content-Range": "bytes %d-%d/*" % (self.uploaded_size,
                                                       (self.uploaded_size+len_data)-1),
                    "Content-Length": str(len_data),
                    "Content-Type": "application/octet-stream",
                    "x-amz-sha256-tree-hash": bytes_to_hex(part_tree_hash),
                    "x-amz-content-sha256": hashlib.sha256(data).hexdigest()
                  }

        # How many times we tried uploading this block
        retries = 0

        while True:
            try:
                response = self.connection.upload_part(
                    self.vault_name,
                    self.uploadid,
                    hashlib.sha256(data).hexdigest(),
                    bytes_to_hex(part_tree_hash),
                    (self.uploaded_size, self.uploaded_size+len_data-1),
                    data)
                response.read()
                break

            except Exception as e:
                if ('408' in e.message or
                    e.code == "ServiceUnavailableException" or
                    e.type == "Server"):

                    uploaded_gb = self.uploaded_size / (1024 ** 1024)
                    if (retries >= constants.BLOCK_RETRIES and
                        retries > math.log10(uploaded_gb) * 10):

                        if self.logger:
                            self.logger.warning("Retries exhausted "\
                                "({}) for this "\
                                "block.".format(constants.BLOCK_RETRIES))
                        raise e

                    if uploaded_gb > 0:
                        retry_per_gb = self.total_retries / uploaded_gb
                    else:
                        retry_per_gb = 0
                    if (self.total_retries >= constants.TOTAL_RETRIES and
                        retry_per_gb > constants.MAX_TOTAL_RETRY_PER_GB):

                        if self.logger:
                            self.logger.warning("Total retries "\
                                "exhausted"\
                                "({}).".format(constants.TOTAL_RETRIES))
                        raise e

                    retries += 1
                    self.total_retries += 1

                    if self.logger:
                        self.logger.warning(e.message)
                        if sys.version_info < (2, 7, 0):
                            self.logger.warning("Total uploaded size "
                                "= {}, block hash = "
                                "{}".format(self.uploaded_size,
                                        bytes_to_hex(part_tree_hash)))
                        else:
                            # Commify large numbers
                            self.logger.warning("Total uploaded size "
                                "= {:,d}, block hash = "
                                "{:}".format(self.uploaded_size,
                                        bytes_to_hex(part_tree_hash)))

                        self.logger.warning("Retries (this block, "
                            "total) = {}/{}, {}/{}".format(retries,
                                    constants.BLOCK_RETRIES,
                                    self.total_retries,
                                    constants.TOTAL_RETRIES))
                        self.logger.warning("Check the AWS status "
                                    "at: http://status.aws.amazon.com/")
                        self.logger.warning('Sleeping %d seconds (%.1f minutes) before retrying this block.' % (constants.SLEEP_TIME, constants.SLEEP_TIME / 60.0))

                    time.sleep(constants.SLEEP_TIME * retries)

                else:
                    self.logger.warning(e.message)
                    self.logger.warning('Not re-trying on this error')
                    raise e

        self.uploaded_size += len(data)

    def close(self):

        if self.closed:
            return

        # Complete the multiplart glacier upload
        response = self.connection.complete_multipart_upload(
                self.vault_name,
                self.uploadid,
                bytes_to_hex(tree_hash(self.tree_hashes)),
                self.uploaded_size)
        self.archive_id = response['ArchiveId']
        self.location = response['Location']
        self.hash_sha256 = bytes_to_hex(tree_hash(self.tree_hashes))
        self.closed = True

    def get_archive_id(self):
        self.close()
        return self.archive_id

    def get_location(self):
        self.close()
        return self.location

    def get_hash(self):
        self.close()
        return self.hash_sha256
