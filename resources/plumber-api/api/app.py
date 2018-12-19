#!/usr/bin/env python3
import plumber as api
from aiohttp import web
from bson import objectid
import asyncio
import logging
import socket
import os
import json

# Application settings

API_HOST="0.0.0.0"
API_PORT=80
STAGES_QTY=int(os.getenv("STAGES_QTY", 0))

# Logging settings

log = logging.getLogger('app')
log.setLevel(logging.DEBUG)

f = logging.Formatter(
        '[{levelname[0]}] [{asctime}] {message}', 
        datefmt = '%d-%m-%Y %H:%M:%S',
	style = '{'
        )
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(f)
log.addHandler(ch)

async def shutdown(server, app, handler):

    server.close()
    await server.wait_closed()
    api.mdb.close()  # database connection close
    await app.shutdown()
    await app.cleanup()

@asyncio.coroutine
async def flush(request):
    """Flush stage queue.

    GET /<stage_number>/flush
    Returns: 200 empty
    """

    
    # Validate stage number
    stage = int(request.match_info['stage'])
    if stage < 1 or stage > STAGES_QTY:
        text = 'Error: wrong stage number'
        log.warning(text)
        return web.Response(status = 400, text = text)

    await api.flush(stage)

    return web.Response()

@asyncio.coroutine
async def healthcheck(request):
    """Check API health.

    GET /_healthcheck

    Returns: 200 empty
    """
    
    return web.Response()

@asyncio.coroutine
async def pop(request):
    """Pop entries from a stage queue.

    GET /<stage_number>/pop

    Parameters:
        
        format: The output format, can be json or plain. Default is json.
        quantity: The number of entries to retrieve. Default is 1.
    
    Returns: 200 with data in JSON or plain text, according to the format argument.
    """

    # Validate stage number
    stage = int(request.match_info['stage'])
    if stage < 1 or stage > STAGES_QTY:
        text = 'Error: wrong stage number'
        log.warning(text)
        return web.Response(status = 400, text = text)

    # Get format (default: json)
    output_format = request.query.get('format', 'json').lower()
    if output_format not in ('json', 'plain'):
        text = 'Error: wrong format parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)

    # Check if must be pushed if older than a number of seconds
    quantity = request.query.get('quantity', '1')
    if not quantity.isdigit():
        text = 'Error: wrong quantity parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)
    quantity = int(quantity)

    json_response = await api.pop(
            stage, 
            quantity
            )

    if output_format == 'json':
        return web.json_response(json_response)
    elif output_format == 'plain':
        return web.Response(text = '\n'.join(json_response))
    else:
        # Never happens
        return web.Response()

@asyncio.coroutine
async def push(request):
    """Push entries to a stage queue.

    POST /<stage_number>/push

    Body: JSON list of objects or text of lines, according to the format argument.
    Parameters:
        
        format: The input format, can be json or plain. Default is json.
        push_if_new: Push only the entries which haven't been previously pushed. Default is disabled.
        push_if_older_than: Push only the entries which haven't been previously pushed or that have been older than a number of seconds. Default is disabled.
    
    Returns: 200 with the number of pushed entries.
    """

    # Validate stage number is not the latest
    stage = int(request.match_info['stage'])
    if stage < 1 or stage > STAGES_QTY:
        text = 'Error: wrong stage number'
        log.warning(text)
        return web.Response(status = 400, text = text)
    
    # Get format (default: json)
    input_format = request.query.get('format', 'json').lower()

    # Check if must be pushed if new
    push_if_new = bool(request.query.get('push_if_new', False))

    # Check if must be pushed if older than a number of seconds
    push_if_older_than = request.query.get('push_if_older_than', '0')
    if not push_if_older_than.isdigit():
        text = 'Error: wrong if_older_than parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)
    push_if_older_than = int(push_if_older_than)

    if input_format == 'json':
        # Validate JSON format
        try:
            json_data = await request.json()
        except Exception as e:
            text = 'Error: can\'t decode JSON input'
            log.warning('%s: %s' % (text, str(e)))
            return web.Response(status = 400, text = text)

        if not isinstance(json_data, (list,)):
            text = 'Error: JSON must be a list of object'
            log.warning('%s: %s' % (text, json_data))
            return web.Response(status = 400, text = text)
    elif input_format == 'plain': 
        # JSON-ify plain text format
        text_data = await request.text()
        json_data = text_data.split("\n") 

    else:
        # Error with an unknown format
        text = 'Error: wrong format parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)

    json_response = await api.push(
            stage, 
            json_data, 
            push_if_new, 
            push_if_older_than
            )

    return web.json_response(json_response);

@asyncio.coroutine
async def store(request):
    """Store an entry to the database.

    POST /<stage_number>/store

    Body: JSON object or text, according to the format argument.

    Parameters:
        
        format: The input and output format, can be json or plain. Default is json.
    
    Returns: 200 with the ID of the stored entry.
    """

    # Validate stage number is not the latest
    stage = int(request.match_info['stage'])
    if stage < 1 or stage > STAGES_QTY:
        text = 'Error: wrong stage number'
        log.warning(text)
        return web.Response(status = 400, text = text)
    
    # Get format (default: json)
    input_format = request.query.get('format', 'json').lower()

    if input_format == 'json':
        # Validate JSON format
        try:
            json_data = await request.json()
        except Exception as e:
            text = 'Error: can\'t decode JSON input'
            log.warning('%s: %s' % (text, str(e)))
            return web.Response(status = 400, text = text)

        if not isinstance(json_data, (dict,list)):
            text = 'Error: JSON must be an object or list'
            log.warning('%s: %s' % (text, json_data))
            return web.Response(status = 400, text = text)

        id_response = await api.store(
                stage, 
                json_data
                )
        return web.json_response(id_response);

    elif input_format == 'plain': 
        # JSON-ify plain text format
        text_data = await request.text()

        id_response = await api.store(
                stage, 
                text_data
                )
        return web.Response(text = id_response)

    else:
        # Error with an unknown format
        text = 'Error: wrong format parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)

@asyncio.coroutine
async def load(request):
    """Load an entry from the database.

    GET /<stage_number>/load

    Parameters:
        
        format: The input and output format, can be json or plain. Default is json.
        filter: The filter JSON object, as accepted by Mongo find_one.
        delete: Delete the matching objects. Default is false.
    
    Returns: 200 with data in JSON or plain text, according to the format argument.
    """

    # Validate stage number
    stage = int(request.match_info['stage'])
    if stage < 1 or stage > STAGES_QTY:
        text = 'Error: wrong stage number'
        log.warning(text)
        return web.Response(status = 400, text = text)

    # Get format (default: json)
    output_format = request.query.get('format', 'json').lower()
    if output_format not in ('json', 'plain'):
        text = 'Error: wrong format parameter'
        log.warning(text)
        return web.Response(status = 400, text = text)

    # Check if must be pushed if new
    delete = bool(request.query.get('delete', False))

    # Validate JSON filter format
    filter_ = request.query.get('filter')
    if not filter_:
        text = 'Error: missing filter'
        log.warning(text)
        return web.Response(status = 400, text = text)
        
    # Validate JSON filter format
    try:
        filter_ = json.loads(filter_)
    except Exception as e:
        text = 'Error: can\'t decode JSON filter'
        log.warning('%s: %s' % (text, str(e)))
        return web.Response(status = 400, text = text)

    if not isinstance(filter_, (dict,)):
        text = 'Error: filter must be a JSON object'
        log.warning('%s: %s' % (text, json_data))
        return web.Response(status = 400, text = text)

    # Objectify _id in case has been searched by id
    if '_id' in filter_:
        filter_['_id'] = objectid.ObjectId(filter_['_id'])

    try:
        json_response = await api.load(
                stage, 
                filter_,
                delete
                )
    except Exception as e:
        text = 'Error: exception on find'
        log.warning('%s: %s' % (text, str(e)))
        return web.Response(status = 400, text = text)

    if output_format == 'json':

        # Empty with no response
        if not json_response:
            return web.json_response({})

        if '_id' in json_response:
            del json_response['_id']
        return web.json_response(json_response['data'])

    elif output_format == 'plain':

        # Empty with no response
        if not json_response:
            return web.Response()

        if '_id' in json_response:
            del json_response['_id']
        return web.Response(text = str(json_response['data']))
    else:
        # Never happens
        return web.Response()

async def init(loop):

    app = web.Application(loop=loop)
    app.router.add_route('POST', '/{stage:\d+}/push', push)
    app.router.add_route('GET', '/{stage:\d+}/pop', pop)
    app.router.add_route('POST', '/{stage:\d+}/store', store)
    app.router.add_route('GET', '/{stage:\d+}/load', load)
    app.router.add_route('POST', '/{stage:\d+}/flush', flush)
    app.router.add_route('GET', '/_healthcheck', healthcheck)

    handler = app.make_handler()

    serv_generator = loop.create_server(handler, API_HOST, API_PORT)
    return serv_generator, handler, app


loop = asyncio.get_event_loop()
serv_generator, handler, app = loop.run_until_complete(init(loop))
serv = loop.run_until_complete(serv_generator)
log.debug('Start server %s' % str(serv.sockets[0].getsockname()))

try:
    loop.run_forever()
except KeyboardInterrupt:
    log.debug('Stop server begin')
finally:
    loop.run_until_complete(shutdown(serv, app, handler))
    loop.close()

log.debug('Stop server end')
