# handle all HTTP / CREST API work:
# input validation, correctly navigating CREST endpoints, rate limiting, async retrieval

from requests_futures.sessions import FuturesSession


def url_format(region_id, req_type):
    url_parent = 'https://crest-tq.eveonline.com/market/'
    if req_type is 'orders':
        url_result = url_parent + region_id + '/orders/all/'
    elif req_type is 'context':
        url_result = url_parent + region_id + '/inventory/types/'
    return url_result


def url_async(url_list, worker_limit):
    worker_limit = 10 if worker_limit > 10 else worker_limit
    session = FuturesSession(max_workers=worker_limit)
    # the line below mistakenly re-serialises the operation and should be fixed immediately JUST SAYIN
    response = (session.get(x).result().json() for x in url_list)
    return response
