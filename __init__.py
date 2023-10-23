from threading import Thread

from datetime import timedelta
import logging

import requests

import voluptuous as vol

from datetime import datetime

from homeassistant.const import (CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

import json as json_lib

# Setting log
_LOGGER = logging.getLogger('ho_mobile_account_init')
_LOGGER.setLevel(logging.DEBUG)

# This is needed, it impacts on the name to be called in configurations.yaml
# Ref: https://developers.home-assistant.io/docs/en/creating_integration_manifest.html
DOMAIN = 'ho_mobile_account'

REQUIREMENTS = ['beautifulsoup4']

OBJECT_ID_CREDIT = 'credit'

CONF_PHONE_NUMBERS = 'phone_numbers'

# Default scan interval = 15 minutes = 900 seconds
DEFAULT_SCAN_INTERVAL = timedelta(seconds=900)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_PHONE_NUMBERS): [cv.string],
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)


# ----------------------------------------------------------------------------------------------------------------------
#
# ASYNC SETUP
#
# ----------------------------------------------------------------------------------------------------------------------


async def async_setup(hass, config):

    #_LOGGER.debug('async_setup() >>> STARTED')

    # create the HoMobile Platform object
    hass.data[DOMAIN] = HoMobilePlatform(hass, config)

    #_LOGGER.debug('async_setup() <<< TERMINATED')

    return True

# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE PLATFORM
#
# ----------------------------------------------------------------------------------------------------------------------


class HoMobilePlatform:

    def __init__(self, hass, config):

        self._hass = hass
        self._config = config

        self._phone_numbers = config[DOMAIN][CONF_PHONE_NUMBERS]
        self._password = config[DOMAIN][CONF_PASSWORD]
        self.update_status_interval = config[DOMAIN][CONF_SCAN_INTERVAL]

        self._credit = {}

        hass.async_create_task(self.async_update_credits())

        hass.async_create_task(self.async_start_timer())

    async def async_start_timer(self):

        # This is used to update the status periodically
        _LOGGER.info('HoMobile credit will be updated each ' + str(self.update_status_interval))

        # Do not put "self.async_update_credits()", with the parenthesis,
        # otherwise you will pass a Coroutine, not a Coroutine function!
        # and get "Coroutine not allowed to be passed to HassJob"
        # Put "self.async_update_credits" without the parenthesis
        async_track_time_interval(
            self._hass,
            self.async_update_credits,
            self.update_status_interval
        )

    # Do not remove now=None, since when async_track_time_interval()
    # calls async_update_credits(), it passes to the function the time!
    async def async_update_credits(self, now=None):

        _LOGGER.debug('Updating HoMobile account credit...')

        threads = []

        for phone_number in self._phone_numbers:
            thread = Thread(
                target=HoMobilePlatform.thread_update_credits,
                args=(phone_number, self._password, self._credit, self._hass)
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    @staticmethod
    def thread_update_credits(phone_number, password, credit, hass):

        # --------------------------------------------------------------------------------------------------------------
        #   FASE 1 - Caricamento della homepage
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'https://www.ho-mobile.it/'

        # session keeping cookies
        session = requests.Session()

        response = session.get(url)

        # get http status code
        http_status_code = response.status_code

        # check response is okay
        if http_status_code != 200:

            _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            _LOGGER.debug(str(response.content))

        else:

            # ----------------------------------------------------------------------------------------------------------
            #   FASE 2 - Recupero dell'accountId dal numero di telefono
            # ----------------------------------------------------------------------------------------------------------

            # login url
            url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

            # set POST https params
            json = {
                'email': None,
                'phoneNumber': phone_number,
                'channel': 'WEB'
            }
            headers = {
                'Referer': 'https://www.ho-mobile.it/',
                'Content-Type': 'application/json'
            }

            response = session.post(url, json=json, headers=headers)

            # get http status code
            http_status_code = response.status_code

            # check response is okay
            if http_status_code != 200:

                _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                # get html in bytes
                _LOGGER.debug(str(response.text))

            else:
                # get html in bytes
                json_str = response.text
                # _LOGGER.debug(json_str)
                json = json_lib.loads(json_str)
                # _LOGGER.debug(str(json))
                _LOGGER.debug('Status is ' + json['operationStatus']['status'])

                if json['operationStatus']['status'] == 'OK':

                    # --------------------------------------------------------------------------------------------------
                    #   FASE 3 - Login tramite accountId e password
                    # --------------------------------------------------------------------------------------------------

                    account_id = json['accountId']

                    # login url
                    url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/login'

                    # set POST https params
                    json = {
                        'accountId': account_id,
                        'email': None,
                        'phoneNumber': phone_number,
                        'password': password,
                        'channel': "WEB",
                        'isRememberMe': False
                    }

                    headers = {
                        'Referer': 'https://www.ho-mobile.it/',
                        'Content-Type': 'application/json'
                    }

                    response = session.post(url, json=json, headers=headers)

                    # get http status code
                    http_status_code = response.status_code

                    # check response is okay
                    if http_status_code != 200:

                        _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                        # get html in bytes
                        _LOGGER.debug(str(response.text))

                    else:
                        # get html in bytes
                        _LOGGER.debug('Username e password inseriti CORRETTAMENTE')

                        # ----------------------------------------------------------------------------------------------
                        #   FASE 3 - Recupero del productId
                        # ----------------------------------------------------------------------------------------------

                        # login url
                        url = 'https://www.ho-mobile.it/leanfe/restAPI/CatalogInfoactivationService/getCatalogInfoactivation'

                        # set POST https params
                        json = {
                            "channel": "WEB",
                            "phoneNumber": phone_number
                        }

                        headers = {
                            'Referer': 'https://www.ho-mobile.it/',
                            'Content-Type': 'application/json'
                        }

                        response = session.post(url, json=json, headers=headers)

                        # get http status code
                        http_status_code = response.status_code

                        # check response is okay
                        if http_status_code != 200:

                            _LOGGER.error(
                                'login page (' + url + ') error: ' + str(http_status_code))

                            # get html in bytes
                            _LOGGER.debug(str(response.text))

                        else:

                            json_str = response.text
                            # _LOGGER.debug(json_str)
                            json = json_lib.loads(json_str)

                            product_id = json['activeOffer']['productList'][0]['productId']

                            # ------------------------------------------------------------------------------------------
                            #   FASE 4 - Recupero dei contatori
                            # ------------------------------------------------------------------------------------------

                            # login url
                            url = 'https://www.ho-mobile.it/leanfe/restAPI/CountersService/getCounters'

                            # set POST https params
                            json = {
                                "channel": "WEB",
                                "phoneNumber": phone_number,
                                "productId": product_id
                            }

                            headers = {
                                'Referer': 'https://www.ho-mobile.it/',
                                'Content-Type': 'application/json'
                            }

                            response = session.post(url, json=json, headers=headers)

                            # get http status code
                            http_status_code = response.status_code

                            # check response is okay
                            if http_status_code != 200:

                                _LOGGER.error('login page (' + url + ') error: ' + str(
                                    http_status_code))

                                # get html in bytes
                                _LOGGER.debug(str(response.text))

                            else:

                                json_str = response.text
                                # _LOGGER.debug(json_str)

                                json = json_lib.loads(json_str)

                                if phone_number not in credit:
                                    credit[phone_number] = {}

                                for item in json['countersList'][0]['countersDetailsList']:
                                    uom = item['residualUnit']
                                    if uom in ['GB','MB']:

                                        # ------------------------------------------------------------------------------
                                        # Recupero dei M/Gbyte residui
                                        # ------------------------------------------------------------------------------
                                        key = 'internet'
                                        value = item['residual']
                                        icon = 'mdi:web'
                                        credit[phone_number][key] = {
                                            'value': value,
                                            'icon': icon,
                                            'uom': uom
                                        }

                                        # ------------------------------------------------------------------------------
                                        # Recupero dei M/Gbyte totali
                                        # ------------------------------------------------------------------------------
                                        key = 'internet_threshold'
                                        value = item['threshold']
                                        icon = 'mdi:web'
                                        credit[phone_number][key] = {
                                            'value': value,
                                            'icon': icon,
                                            'uom': uom
                                        }

                                # ------------------------------------------------------------------------------
                                # Recupero della data di prossimo rinnovo
                                # ------------------------------------------------------------------------------

                                # Current Epoch Unix Timestamp (ad es. 1698184800000)
                                renewal_ts = json['countersList'][0]['productNextRenewalDate'] / 1000

                                key = 'internet_renewal'
                                value = datetime.fromtimestamp(renewal_ts).strftime('%Y-%m-%d')
                                icon = 'mdi:calendar-clock'
                                credit[phone_number][key] = {
                                    'value': value,
                                    'icon': icon,
                                    'uom': ''
                                }

                                for k, v in credit[phone_number].items():
                                    if v['value'] is not None:
                                        pnk = phone_number + '_' + k
                                        _LOGGER.info(pnk + ': ' + str(v['value']))
                                        attributes = {
                                            'icon': v['icon'],
                                            'unit_of_measurement': v['uom']
                                        }
                                        hass.states.async_set(DOMAIN + "." + pnk, v['value'], attributes)
