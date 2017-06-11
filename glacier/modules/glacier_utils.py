#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
import csv
import json
import sys
from prettytable import PrettyTable


# import our modules
from modules.GlacierWrapper import GlacierWrapper
from modules import constants

# function definition
def default_glacier_wrapper(args, **kwargs):
    """
    Convenience function to call an instance of GlacierWrapper
    with all required arguments.
    """
    return GlacierWrapper(args.aws_access_key,
                          args.aws_secret_key,
                          args.region,
                          bookkeeping=args.bookkeeping,
                          no_bookkeeping=args.no_bookkeeping,
                          bookkeeping_domain_name=args.bookkeeping_domain_name,
                          sdb_access_key=args.sdb_access_key,
                          sdb_secret_key=args.sdb_secret_key,
                          sdb_region=args.sdb_region,
                          # sns_enable=args.sns_enable,
                          # sns_topic=args.sns_topic,
                          # sns_monitored_vaults=args.sns_monitored_vaults,
                          # sns_options=args.sns_options,
                          # config_object=args.config_object,
                          logfile=args.logfile,
                          loglevel=args.loglevel,
                          logtostdout=args.logtostdout)

def output_msg(msg, output, success=True):
    """
    In case of a single message output, e.g. nothing found.

    :param msg: a single message to output.
    :type msg: str
    :param success: whether the operation was a success or not.
    :type success: boolean
    :param output: output format
    :type output: string
    :raises: ValueError if output not in constants.TABLE_OUTPUT_FORMAT
    :returns :nothing, prints the output or sys.exist with status 125
    """

    if output not in constants.TABLE_OUTPUT_FORMAT:
        raise ValueError("Output format must be{}, "
                         "got {}".format(constants.TABLE_OUTPUT_FORMAT,
                                         output))

    if msg is not None:
        if output == 'print':
            print msg

        if output == 'csv':
            csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
            csvwriter.writerow(msg)

        if output == 'json':
            print json.dumps(msg)

    if not success:
        sys.exit(125)

def size_fmt(num, decimals = 1):
    """
    Formats file sizes in human readable format. Anything bigger than
    TB is returned is TB. Number of decimals is optional,
    defaults to 1.

    :param num: value to be converted
    :type num: int
    :decimals: number of decimals to consider
    :type decimals: int
    :returns: formatted number
    :returns type: string
    """

    fmt = "%%3.%sf %%s"% decimals
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return fmt % (num, x)

        num /= 1024.0

    return fmt % (num, 'TB')


def output_headers(headers, output):
    """
    Prints a list of headers - single item output.

    :param headers: the output to be printed as {'header1':'data1',...}
    :type headers: dict
    :param output: selects output type, must be
    listed in constants.HEADERS_OUTPUT_FORMAT
    :type output: string
    :raises: ValueError when output format is not supported
    """

    if output not in constants.HEADERS_OUTPUT_FORMAT:
        raise ValueError("Output must be in {}, got"
                         ":{}".format(constants.HEADERS_OUTPUT_FORMAT,
                                      output))
    rows = [(k, headers[k]) for k in headers.keys()]
    if output == 'print':
        table = PrettyTable(["Header", "Value"])
        for row in rows:
            if len(str(row[1])) <= 138:
                table.add_row(row)

        print table

    if output == 'csv':
        csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
        for row in rows:
            csvwriter.writerow(row)

    if output == 'json':
        print json.dumps(headers)

def output_table(results, output, keys=None, sort_key=None):
    """
    Prettyprints results. Expects a list of identical dicts.
    Use the dict keys as headers unless keys is given;
    one line for each item.

    Expected format of data is a list of dicts:
    [{'key1':'data1.1', 'key2':'data1.2', ... },
     {'key1':'data1.2', 'key2':'data2.2', ... },
     ...]
    :param keys: dict of headers to be printed for each key:
    {'key1':'header1', 'key2':'header2',...}
    :type keys: dict
    :param sort_key: the key to use for sorting the table.
    :type sort_key: string
    :raises : ValueError if output not in constants.TABLE_OUTPUT_FORMAT
    :returns: nothing, prints the output on the console
    """

    if output not in constants.TABLE_OUTPUT_FORMAT:
        raise ValueError("Output format must be{}, "
                         "got {}".format(constants.TABLE_OUTPUT_FORMAT,
                                         output))
    if output == 'print':
        if len(results) == 0:
            print 'No output!'
            return

        headers = [keys[k] for k in keys.keys()] if keys else results[0].keys()
        table = PrettyTable(headers)
        for line in results:
            table.add_row([line[k] if k in line else '' for k in (keys.keys() if keys else headers)])

        if sort_key:
            table.sortby = keys[sort_key] if keys else sort_key

        print table

    if output == 'csv':
        csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
        keys = results[0].keys()
        csvwriter.writerow(keys)
        for row in results:
            csvwriter.writerow([row[k] for k in keys])

    if output == 'json':
        print json.dumps(results)
