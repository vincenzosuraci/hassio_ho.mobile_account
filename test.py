import os
# Questo wokaround funziona sul PC ma non in Home Assistant
os.environ.setdefault('AIOHTTP_NO_EXTENSIONS', '1')

import datetime
from datetime import timedelta
import logging

import sys

from aiohttp import ClientResponseError

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

import aiohttp
import asyncio
import voluptuous as vol

import json as JSON

# Setting log
_LOGGER = logging.getLogger('ho_mobile_account_init')
_LOGGER.setLevel(logging.DEBUG)

# This is needed, it impacts on the name to be called in configurations.yaml
# Ref: https://developers.home-assistant.io/docs/en/creating_integration_manifest.html
DOMAIN = 'ho_mobile_account'

REQUIREMENTS = ['beautifulsoup4']

OBJECT_ID_CREDIT = 'credit'

CONF_PHONE_NUMBER = 'phone_number'

DEFAULT_SCAN_INTERVAL = timedelta(seconds=900)


class HoMobilePlatform:

    def __init__(self):
        self._phoneNumber = '3519271620'
        self._password = '58J%u#krw97WDy!W'

        self._credit = {}

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_update_credits())

    async def async_update_credits(self):
        _LOGGER.debug('Updating HoMobile account credit...')

        # --------------------------------------------------------------------------------------------------------------
        #   FASE 1 - Caricamento della homepage
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'https://www.ho-mobile.it/'

        # Session keeping cookies
        async with aiohttp.ClientSession() as session:

            # Aggiornamento del 29/07/2022
            #
            # Sembra che il sito web https://www.ho-mobile.it/ risponda con qualche carattere corrotto nell'header
            # Questo fa fallire il comando session.get(url) con il seguente errore:
            # aiohttp.client_exceptions.ClientResponseError: 400, message='Invalid header value char', url=URL('https://www.ho-mobile.it/')
            #
            # Il workaorund è quello di impostare la variabile di ambiente AIOHTTP_NO_EXTENSIONS = 1
            # Ma, purtroppo, non funziona in Home Assistant!

            async with session.get(url) as response:

                # get http status code
                http_status_code = response.status

                # check response is okay
                if http_status_code != 200:

                    _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                    # get html in bytes
                    _LOGGER.debug(str(response.content))

                else:

                    # --------------------------------------------------------------------------------------------------
                    #   FASE 2 - Recupero dell'accountId dal numero di telefono
                    # --------------------------------------------------------------------------------------------------

                    # login url
                    url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

                    # set POST https params
                    json = {
                        'email': None,
                        'phoneNumber': self._phoneNumber,
                        'channel': 'WEB'
                    }
                    headers = {
                        'Referer': 'https://www.ho-mobile.it/',
                        'Content-Type': 'application/json'
                    }

                    async with session.post(url, json=json, headers=headers) as response:

                        # get http status code
                        http_status_code = response.status

                        # check response is okay
                        if http_status_code != 200:

                            _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                            # get html in bytes
                            _LOGGER.debug(str(await response.text()))

                        else:
                            # get html in bytes
                            json_str = await response.text()
                            # _LOGGER.debug(json_str)
                            json = JSON.loads(json_str)
                            # _LOGGER.debug(str(json))
                            _LOGGER.debug('Status is ' + json['operationStatus']['status'])

                            if json['operationStatus']['status'] == 'OK':

                                # --------------------------------------------------------------------------------------
                                #   FASE 3 - Login tramite accountId e password
                                # --------------------------------------------------------------------------------------

                                accountId = json['accountId']

                                # login url
                                url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/login'

                                # set POST https params
                                json = {
                                    'accountId': accountId,
                                    'email': None,
                                    'phoneNumber': self._phoneNumber,
                                    'password': self._password,
                                    'channel': "WEB",
                                    'isRememberMe': False
                                }

                                headers = {
                                    'Referer': 'https://www.ho-mobile.it/',
                                    'Content-Type': 'application/json'
                                }

                                async with session.post(url, json=json, headers=headers) as response:

                                    # get http status code
                                    http_status_code = response.status

                                    # check response is okay
                                    if http_status_code != 200:

                                        _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                                        # get html in bytes
                                        _LOGGER.debug(str(await response.text()))

                                    else:
                                        # get html in bytes
                                        _LOGGER.debug('Username e password inseriti CORRETTAMENTE')

                                        # ------------------------------------------------------------------------------
                                        #   FASE 3 - Recupero del productId
                                        # ------------------------------------------------------------------------------

                                        # login url
                                        url = 'https://www.ho-mobile.it/leanfe/restAPI/CatalogInfoactivationService/getCatalogInfoactivation'

                                        # set POST https params
                                        json = {
                                            "channel": "WEB",
                                            "phoneNumber": self._phoneNumber
                                        }

                                        headers = {
                                            'Referer': 'https://www.ho-mobile.it/',
                                            'Content-Type': 'application/json'
                                        }

                                        async with session.post(url, json=json, headers=headers) as response:

                                            # get http status code
                                            http_status_code = response.status

                                            # check response is okay
                                            if http_status_code != 200:

                                                _LOGGER.error(
                                                    'login page (' + url + ') error: ' + str(http_status_code))

                                                # get html in bytes
                                                _LOGGER.debug(str(await response.text()))

                                            else:

                                                json_str = await response.text()
                                                # _LOGGER.debug(json_str)
                                                json = JSON.loads(json_str)

                                                productId = json['activeOffer']['productList'][0]['productId']

                                                # --------------------------------------------------------------------------------------------------
                                                #   FASE 4 - Recupero dei contatori
                                                # --------------------------------------------------------------------------------------------------

                                                # login url
                                                url = 'https://www.ho-mobile.it/leanfe/restAPI/CountersService/getCounters'

                                                # set POST https params
                                                json = {
                                                    "channel": "WEB",
                                                    "phoneNumber": self._phoneNumber,
                                                    "productId": productId
                                                }

                                                headers = {
                                                    'Referer': 'https://www.ho-mobile.it/',
                                                    'Content-Type': 'application/json'
                                                }

                                                async with session.post(url, json=json,
                                                                        headers=headers) as response:

                                                    # get http status code
                                                    http_status_code = response.status

                                                    # check response is okay
                                                    if http_status_code != 200:

                                                        _LOGGER.error('login page (' + url + ') error: ' + str(
                                                            http_status_code))

                                                        # get html in bytes
                                                        _LOGGER.debug(str(await response.text()))

                                                    else:

                                                        json_str = await response.text()
                                                        # _LOGGER.debug(json_str)

                                                        json = JSON.loads(json_str)

                                                        for item in json['countersList'][0]['countersDetailsList']:
                                                            uom = item['residualUnit']
                                                            if uom == 'GB':
                                                                key = 'internet'
                                                                value = item['residual']
                                                                icon = 'mdi:web'
                                                                self._credit[key] = {
                                                                    'value': value,
                                                                    'icon': icon,
                                                                    'uom': uom}

                                                                key = 'internet_threshold'
                                                                value = item['threshold']
                                                                icon = 'mdi:web'
                                                                self._credit[key] = {
                                                                    'value': value,
                                                                    'icon': icon,
                                                                    'uom': uom}

                                                                key = 'internet_renewal'
                                                                value = item['nextResetDate']
                                                                icon = 'mdi:calendar-clock'
                                                                self._credit[key] = {
                                                                    'value': value,
                                                                    'icon': icon,
                                                                    'uom': ''}

                                                        for k, v in self._credit.items():
                                                            if v['value'] is not None:
                                                                _LOGGER.info(k + ': ' + str(v['value']))
                                                                attributes = {"icon": v['icon'],
                                                                              'unit_of_measurement': v['uom']}
                                                                # self._hass.states.async_set(DOMAIN + "." + k, v['value'], attributes)
                                                        return True

        return False


HMP = HoMobilePlatform()
