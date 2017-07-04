#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from modules.glacier_utils import default_glacier_wrapper

# function definition

def snssync(args):
    """
    If monitored_vaults is specified in configuration file, subscribe
    vaults specificed in it to notifications, otherwiser
    subscribe all vault.
    """

    glacier = default_glacier_wrapper(args)
    response = glacier.sns_sync(sns_options=args.sns_options,
                                output=args.output)
    output_table(response, args.output)

def snssubscribe(args):
    """
    Subscribe individual vaults to notifications by method
    specified by user.
    """

    protocol = args.protocol
    endpoint = args.endpoint
    vault_names = args.vault
    topic = args.topic

    glacier = default_glacier_wrapper(args)
    response = glacier.sns_subscribe(protocol, endpoint, topic,
                                     vault_names=vault_names,
                                     sns_options=args.sns_options)
    output_table(response, args.output)

def snslistsubscriptions(args):
    """
    List subscriptions.
    """

    protocol = args.protocol
    endpoint = args.endpoint
    topic = args.topic

    glacier = default_glacier_wrapper(args)
    response = glacier.sns_list_subscriptions(protocol,
                    endpoint, topic, sns_options=args.sns_options)
    output_table(response, args.output)

def snslisttopics(args):
    """
    List subscriptions.
    """

    glacier = default_glacier_wrapper(args)
    response = glacier.sns_list_topics(sns_options=args.sns_options)
    output_table(response, args.output)

def snsunsubscribe(args):
    """
    Unsubscribe individual vaults from notifications for
    specified protocol, endpoint and vault.
    """

    protocol = args.protocol
    endpoint = args.endpoint
    topic = args.topic

    glacier = default_glacier_wrapper(args)
    response = glacier.sns_unsubscribe(protocol, endpoint,
                    topic, sns_options=args.sns_options)
    output_table(response, args.output)
