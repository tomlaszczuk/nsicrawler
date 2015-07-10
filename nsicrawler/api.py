"""
nsicrawler.api

Module that implements api for nsi web crawling
"""

import requests
from bs4 import BeautifulSoup as Soup


def available_contract_conditions(url, segmentation):
    """
    Provides list of contract condition codes
    """
    contract_conditions = []
    r = requests.post(url, data={'processSegmentationCode': segmentation})
    available_cc = r.json()['pageInfo']['availableContractConditions']
    for cc in available_cc:
        contract_condition = cc["value"].split()[0]
        if "MIX" in segmentation:
            contract_condition += "V"
        else:
            contract_condition += "A"
        contract_conditions.append(contract_condition)
    return contract_conditions


def __convert_to_proper_json(offers):
    """
    Helper function. Rename two dictonary keys for unification.
    """
    for offer in offers:
        offer['offerNSICode'] = offer['offerCode']
        offer['monthlyFeeGross'] = offer['tariffPlanCode'][-2:]
    return offers


def offer_list(url, segmentation, contract_conditions):
    """
    Return a json representation of offers.
    """
    offer_json_repr = []
    for contract_condition in contract_conditions:
        r = requests.post(
            url,
            data={
                "processSegmentationCode": segmentation,
                "contractConditionCode": contract_condition
            }
        )
        offers = r.json()['rotator']
        if not offers:  # handler for mix
            offers = r.json()['sliderPositions']['0']
            offers = __convert_to_proper_json(offers)
        offer_json_repr.extend(offers)
    return offer_json_repr


def pages(url, segmentation, offer):
    """
    Provides number of pages to scrape
    """
    r = requests.post(
        url,
        data={"processSegmentationCode": segmentation,
              "offerNSICode": offer['offerNSICode'],
              "tariffPlanCode": offer['tariffPlanCode'],
              "contractConditionCode": offer['contractConditionCode']}
    )
    return r.json()['pageInfo']['pages']


def __build_product_page_from_params(**params):
    """
    Helper function. Builds product page url from provided params dict
    """
    url = 'http://plus.pl/'
    if 'SOHO' in params['processSegmentationCode']:
        url += 'dla-firm/'
    if params['deviceTypeCode'] == 'TAB':
        url += 'tablet-laptop?'
    elif params['deviceTypeCode'] == 'MODEM':
        url += 'modem-router?'
    else:
        url += 'telefon?'
    url += "&".join(["%s=%s" % (key, params[key]) for key in params])
    return url


def __add_product_page_to_devices(segmentation, offer, devices):
    """
    Helper function. This one injects product page to each one of device
    elements in devices dict
    """
    for device in devices:
        device['product_page_url'] = __build_product_page_from_params(
            processSegmentationCode=segmentation,
            offerNSICode=offer['offerNSICode'],
            tariffPlanCode=offer['tariffPlanCode'],
            contractConditionCode=offer['contractConditionCode'],
            deviceTypeCode=device['productType'],
            deviceStockCode=device['sku'],
            marketTypeCode=segmentation.split('.')[0]
        )
    return devices


def __find_all_skus_for_device_in_offer(product_page, sku_stock_code):
    """
    Return a list of all sku stock codes for provided product page url
    """
    r = requests.get(url=product_page)
    html = r.content
    parsed_html = Soup(html,"html.parser")
    skus = parsed_html.find_all('input', attrs={'name': 'color'})
    return [sku['device-skus'] for sku in skus] or [sku_stock_code]


def __add_all_skus_for_all_devices_in_offer(devices):
    """
    Injects list of all skus for devices dict
    """
    for device in devices:
        device['skus'] = __find_all_skus_for_device_in_offer(
            device['product_page_url'], device['sku'])
    return devices


def __add_old_price_info_for_devices_in_offer(url, offer, devices):
    """
    Injects old price elem for all devices in offer
    """
    for device in devices:
        old_price = None
        prices_repr = check_product_prices(
            url,
            device['sku'],
            offer['offerNSICode'],
            offer['tariffPlanCode'],
            offer['contractConditionCode']
        )
        if prices_repr:
            prices = prices_repr[0].get('pricesTransport', [])
            for price in prices:
                if price.get('code') == 'OLD':
                    old_price = price.get('grossPrice')
                    break
        if old_price:
            device['old_price'] = old_price
    return devices


def devices_in_offer(url, segmentation, offer, page_count,
                     check_price_portlet_url):
    """
    Provides json representation of all devices available to buy in offer
    """
    all_devices = []
    for page in range(1, page_count+1):
        r = requests.post(
            url,
            data={"processSegmentationCode": segmentation,
                  "offerNSICode": offer['offerNSICode'],
                  "tariffPlanCode": offer['tariffPlanCode'],
                  "contractConditionCode": offer['contractConditionCode'],
                  "page": page}
        )
        devices = r.json()['devices']
        devices = __add_product_page_to_devices(segmentation, offer, devices)
        devices = __add_all_skus_for_all_devices_in_offer(devices)
        devices = __add_old_price_info_for_devices_in_offer(
            check_price_portlet_url, offer, devices)
        all_devices.extend(devices)
    return all_devices


def __add_prefix(url):
    if not url.startswith('http://'):
        url = 'http://plus.pl' + url
    return url


def find_main_photo_for_sku(product_page):
    """
    Finds main photo in provided product page url.
    Product page url should contain deviceTypeCode and deviceStockCode params
    """
    r = requests.get(product_page)
    html = r.content
    parsed_html = Soup(html, "html.parser")
    photo_container = parsed_html.find('div', attrs={'id': 'phone-carousel'})
    img = photo_container.find('img')
    return __add_prefix(img.attrs['src'])


def check_availability(url, stock_code):
    """
    Return string repr for sku availability
    """
    r = requests.post(url,
                      data={'deviceStockCode': stock_code})
    return r.json()['deviceAvailables'][0]['available']


def check_product_prices(url, stock_code, offer_nsi_code,
                         tariff_plan_code, contract_condition_code):
    """
    Return json repr of product prices
    """
    r = requests.post(url, data={
        'deviceStockCode': stock_code,
        'offerNSICode': offer_nsi_code,
        'tariffPlanCode': tariff_plan_code,
        'contractConditionCode': contract_condition_code
    })
    return r.json()['devicesPrices']