import time
import requests
from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
import arrow
import json
import csv
from os import path

c_str = lambda x: "{:,}".format(x)
base_dir = path.dirname(path.realpath('__file__'))


def market_configs(hub_spec):
    region = {
        'jita': [10000002, 60003760],
        'amarr': [10000043, 60008494],
        'dodixie': [10000032, 60011866],
        'hek': [10000042, 60005686],
        'rens': [10000030, 60004588]
    }
    hub_choice = region[hub_spec]
    return hub_choice


def url_format(region_spec):
    url_base = 'https://crest-tq.eveonline.com/market/' + region_spec + '/orders/all/'
    return url_base


def url_async(url_list, worker_limit):
    if worker_limit > 10:
        worker_limit = 10
    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=worker_limit))
    response = (session.get(x).result().json() for x in url_list)
    return response


def group_dictvalue(raw_list, dictvalue):
    new_dict = {}
    for i in raw_list:
        new_key = i.pop(dictvalue)
        if new_key in new_dict:
            new_dict[new_key].append(i)
        else:
            new_dict[new_key] = [i]
    return new_dict


def csv_makedict(f_dir, f_name, k, v, enc):
    with open(path.join(f_dir, f_name), mode='r', encoding=enc) as csv_input:
        csv_read = csv.reader(csv_input)
        csv_dict = {rows[k]: rows[v] for rows in csv_read}
        return csv_dict


def market_import(hub_spec):
    t_import = time.time()
    data_configs = market_configs(hub_spec)
    hub_regionid = str(data_configs[0])
    url_base = url_format(hub_regionid)
    url_market = url_base + '?page='
    print('\nMARKET_IMPORT: Trying: %s' % url_base)
    data_pages = requests.get(url_base).json()['pageCount']
    print('MARKET_IMPORT: %s pages found.' % (str(data_pages)))
    url_set = [url_market + str(x) for x in range(1, data_pages+1)]
    data_res = url_async(url_set, data_pages)
    data_items = [x for i in data_res for x in i['items']]
    print('MARKET_IMPORT: %s total entries combined.' % (c_str(len(data_items))))
    print("--- %s seconds ---\n" % (time.time() - t_import))
    return data_items, data_configs


def market_distill(raw_list, configs):
    t_hub = time.time()
    print('MARKET_DISTILL: Purging all non-hub orders.')
    data_total = raw_list
    hub_stationid = configs[1]
    data_hubonly = [x for x in data_total if hub_stationid == x['stationID']]
    print('MARKET_DISTILL: %s entries preserved; %s entries purged.'
          % (c_str(len(data_hubonly)), c_str(len(raw_list) - len(data_hubonly))))
    print("--- %s seconds ---\n" % (time.time() - t_hub))
    t_timestamp = time.time()
    print('MARKET_DISTILL: Converting order times to integer timestamps with Arrow.')
    data_timestamp = data_hubonly
    for i in range(0, len(data_hubonly)):
        order_time = arrow.get(data_hubonly[i]['issued'])
        data_timestamp[i]['issued'] = order_time.timestamp
    print('MARKET_DISTILL: %s total entries updated.' % (c_str(len(data_timestamp))))
    print("--- %s seconds ---\n" % (time.time() - t_timestamp))
    t_typesort = time.time()
    print('MARKET_DISTILL: Grouping all orders by their typeID.')
    sort_choice = 'type'
    data_grouped_type = group_dictvalue(data_timestamp, sort_choice)
    print('MARKET_DISTILL: %s total entries grouped by %s unique typeIDs.'
          % (c_str(len(data_timestamp)), c_str(len(data_grouped_type))))
    print("--- %s seconds ---\n" % (time.time() - t_typesort))
    t_buysell = time.time()
    print('MARKET_DISTILL: Separating each typeID\'s orders into Buy and Sell.')
    data_grouped_buysell = {}
    sort_choice = 'buy'
    for k,v in data_grouped_type.items():
        buysell_grouped = group_dictvalue(v, sort_choice)
        data_grouped_buysell[k] = [buysell_grouped]
    print('MARKET_DISTILL: %s order groups separated.'
          % (c_str(len(data_grouped_buysell.values()))))
    print("--- %s seconds ---\n" % (time.time() - t_buysell))
    return data_grouped_buysell


def market_context(raw_list):
    context_namelist = csv_makedict('resources', 'invTypes_small.csv', 0, 2, 'utf-8')
    # take out the station value from each
    # make a new list that contains:
    # - name that corresponds w/ ID
    # - station id
    # - pricing/volume info
    # add to dict such that {'typeid': [[orders],[context]]
    data_contextualised = ''
    return data_contextualised


def write_json(data_input):
    t_p_json = time.time()
    print('WRITE_JSON: Writing JSON to file.')
    with open(path.join('json', "orderbook_" + str(time.time()) + ".txt"), "w") as f_output:
        json.dump(data_input, f_output, indent=4)
    print("--- %s seconds ---\n" % (time.time() - t_p_json))


def write_db():
    # write data structure to database
    pass

t0 = time.time()

orders_raw, orders_config = market_import('rens')
orders_structured = market_distill(orders_raw, orders_config)
orders_contextualised = market_context(orders_structured)

write_json(orders_structured)

print("Operation complete in %s seconds." % (time.time() - t0))
