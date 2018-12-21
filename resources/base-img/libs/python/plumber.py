#!/usr/bin/env python3
import pymongo
import os
import datetime
import sys
import logging

MONGO_HOST="mongodb://mongo:27017/"

mdb =  None

log = logging.getLogger('app')

def _lazy_connect():
    global mdb

    if not mdb:
        mdb = pymongo.MongoClient(MONGO_HOST)

async def flush(stage):
    """
    Flush stage queue.
    """

    _lazy_connect()

    mdb['stage-%d' % stage].incoming.drop()

    log.debug('stage-%d delete' % (stage))


async def pop(stage, quantity = 1):
    """Pop entries from a stage queue.

    Parameters:
        
        stage: The number of the stage queue.
        quantity: The number of entries to retrieve. Default is 1.
    
    Returns the data objects.
    """

    _lazy_connect()

    results = []
    
    for i in range(quantity):
        
        result = mdb['stage-%d' % stage].incoming.find_one_and_update(
                filter = { '_consumed': False },
                update = { '$set': { '_consumed': True } },
                sort = [('_id', 1)]
            )

        if result:
            results.append(result['data'])

    log.debug(
            'stage-%d pops %d/%d' % (
                stage, 
                len(results),
                quantity
                )
            )
    return results

async def push(stage, entry_list, push_if_new = False, push_if_older_than = 0):
    """Push entries to a stage queue.

    Parameters:
        
        stage: The number of stage queue.
        entry_list: List of objects.
        push_if_new: Push only the entries which haven't been previously pushed. Default is false.
        push_if_older_than: Push only the entries which haven't been previously pushed or that have been older than a number of seconds. Default is 0 (disabled).
    
    Returns: the number of pushed entries.
    """

    _lazy_connect()

    # Silently exit on empty lists
    if not entry_list:
        return []

    # Manage push-if-new actions
    if push_if_new:

        modified_or_inserted = 0
        for entry in entry_list:
            
            filterdata = { 'data': entry }

            newdata = { 
                    '_time': datetime.datetime.utcnow(),
                    '_consumed': False,
                    'data': entry 
                }
            
            result = mdb['stage-%d' % stage].incoming.update_one(
                    filter = filterdata,
                    update = { '$setOnInsert': newdata }, 
                    upsert = True
                )

            modified_or_inserted += result.modified_count + int(bool(result.upserted_id))

        log.debug(
                'pushed to stage-%d (if-new) %d/%d' % (
                    stage, 
                    modified_or_inserted, 
                    len(entry_list)
                    )
                )
        return modified_or_inserted
     

    elif push_if_older_than:

        modified_or_inserted = 0
        for entry in entry_list:

            filterdata = {
                '$and': [
                    { 'data': entry },
                    { '_time': { 
                        # It's $gt because we want to match the newer data, and $setOnInsert
                        # if it doesn't match.
                        '$gt': datetime.datetime.utcnow() - datetime.timedelta(
                            seconds = push_if_older_than
                        ) 
                        } 
                    }
                ]
            }

            newdata = { 
                '_time': datetime.datetime.utcnow(),
                '_consumed': False,
                'data': entry 
            }

            result = mdb['stage-%d' % stage].incoming.update_one(
                    filter = filterdata,
                    update = { '$setOnInsert': newdata }, 
                    upsert = True
                )

            modified_or_inserted += result.modified_count + int(bool(result.upserted_id))

        log.debug(
                'pushed to stage-%d (if-older-than %d) %d/%d' % (
                    stage, 
                    push_if_older_than,
                    modified_or_inserted, 
                    len(entry_list)
                    )
                )
        return modified_or_inserted
    else:

        
        formatted_entries = [ 
                { 
                    '_time': datetime.datetime.utcnow(),
                    '_consumed': False,
                    'data': entry 
                } for entry in entry_list 
            ]
        
        result = mdb['stage-%d' % stage].incoming.insert_many(
                formatted_entries
                    )

        log.debug(
                'pushed to stage-%d %d/%d' % (
                    stage, 
                    len(result.inserted_ids),
                    len(entry_list)
                    )
                )

        return len(result.inserted_ids)

async def store(stage, json_data):
    """Store an entry to the database.

    Parameters:
        
        stage: The number of stage queue.
        json_data: The entry object.
    
    Returns the Mongo ObjectID of the insterted object in string format.
    """

    _lazy_connect()
            
    result = mdb['stage-%d' % stage].storage.insert_one(
            document = { 'data': json_data }
        )

    log.debug(
            'stored to stage-%d' % (
                stage, 
                )
            )

    return str(result.inserted_id)

async def load(stage, filter_, delete):
    """Load an entry from the database.

    Parameters:
        
        stage: The number of stage queue.
        filter_: The filter JSON object, as accepted by Mongo find_one.
        delete: Delete the matching objects.
    
    Returns: the requested entry object.
    """

    _lazy_connect()
            
    if delete:
        result = mdb['stage-%d' % stage].storage.find_one_and_delete(
            filter = filter_
        )
    else:
        result = mdb['stage-%d' % stage].storage.find_one(
            filter = filter_
        )

    deleted_text = ' and deleted' if delete else ''

    if result:
        log.debug(
                'loaded%s from stage-%d 1/1' % (
                    deleted_text,
                    stage, 
                    )
                )
        result['_id'] = str(result['_id'])
        return result
    else:
        log.debug(
                'loaded%s from stage-%d 0/1' % (
                    deleted_text,
                    stage, 
                    )
                )

