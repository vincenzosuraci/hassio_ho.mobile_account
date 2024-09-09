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

    # create the HoMobile Platform object
    hass.data[DOMAIN] = HoMobilePlatform(hass, config, DOMAIN)

    return True


# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE CRAWLER
#
# ----------------------------------------------------------------------------------------------------------------------

class HoMobileCrawler:

    def __init__(self, password):
        self._password = password
        self._credit = {}

    @property
    def password(self):
        return self._password

    @property
    def credit(self):
        return self._credit

    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    @staticmethod
    def save_info(pnk, v, attributes):
        pass

    def get_phone_number_credit(self, phone_number):

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

            self.error('login page (' + url + ') error: ' + str(http_status_code))

            # get html in bytes
            self.debug(str(response.content))

        else:

            # ----------------------------------------------------------------------------------------------------------
            #   FASE 2 - Recupero dell'accountId dal numero di telefono
            # ----------------------------------------------------------------------------------------------------------

            # login url
            url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

            # set POST https params
            json = {
                "email": None,
                "phoneNumber": phone_number,
                "channel": "WEB"
            }
            headers = {

                "Content-Type": "application/json",
                "User-Agent": "HomeAssistant",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.ho-mobile.it/",

            }

            response = session.post(url, json=json, headers=headers)

            # get http status code
            http_status_code = response.status_code

            # check response is okay
            if http_status_code != 200:

                self.error('login page (' + url + ') error: ' + str(http_status_code))

                # get html in bytes
                self.debug(str(response.text))

            else:
                # get html in bytes
                json_str = response.text
                json = json_lib.loads(json_str)
                status = json['operationStatus']['status']
                self.debug('Phone number ' + str(phone_number) + ' status is ' + status)
                if status != 'OK':

                    diagnostic = json['operationStatus']['diagnostic']
                    errorCode = json['operationStatus']['errorCode']
                    self.debug('Phone number ' + str(phone_number) +
                               ' errorCode: ' + errorCode +
                               ' - diagnostic: ' + diagnostic
                               )

                else:

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
                        'password': self.password,
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

                        self.error('login page (' + url + ') error: ' + str(http_status_code))

                        # get html in bytes
                        self.debug(str(response.text))

                    else:
                        # get html in bytes
                        self.debug('Username e password inseriti CORRETTAMENTE')

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

                            self.error(
                                'login page (' + url + ') error: ' + str(http_status_code))

                            # get html in bytes
                            self.debug(str(response.text))

                        else:

                            json_str = response.text
                            # self.debug(json_str)
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

                                self.error('login page (' + url + ') error: ' + str(
                                    http_status_code))

                                # get html in bytes
                                self.debug(str(response.text))

                            else:

                                json_str = response.text
                                # self.debug(json_str)

                                json = json_lib.loads(json_str)

                                if phone_number not in self.credit:
                                    self.credit[phone_number] = {}

                                for item in json['countersList'][0]['countersDetailsList']:
                                    uom = item['residualUnit']
                                    if uom in ['GB', 'MB']:
                                        # ------------------------------------------------------------------------------
                                        # Recupero dei M/Gbyte residui
                                        # ------------------------------------------------------------------------------
                                        key = 'internet'
                                        value = item['residual']
                                        icon = 'mdi:web'
                                        self.credit[phone_number][key] = {
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
                                        self.credit[phone_number][key] = {
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
                                value = datetime.fromtimestamp(renewal_ts).strftime('%d/%m/%Y')
                                icon = 'mdi:calendar-clock'
                                self.credit[phone_number][key] = {
                                    'value': value,
                                    'icon': icon,
                                    'uom': ''
                                }

                                for k, v in self.credit[phone_number].items():
                                    if v['value'] is not None:
                                        pnk = phone_number + '_' + k
                                        self.info(pnk + ': ' + str(v['value']))
                                        attributes = {
                                            'icon': v['icon'],
                                            'unit_of_measurement': v['uom']
                                        }
                                        self.save_info(pnk, v, attributes)

# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE PLATFORM
#
# ----------------------------------------------------------------------------------------------------------------------


class HoMobilePlatform(HoMobileCrawler):

    def __init__(self, hass, config, domain):

        self._hass = hass
        self._config = config
        self._domain = domain
        self._name = 'HoMobile'

        super().__init__(
            password = self.config[self.domain][CONF_PASSWORD],
        )

        self._update_status_interval = self.config[self.domain][CONF_SCAN_INTERVAL]

        self.hass.async_create_task(self.async_update_credits())

        self.hass.async_create_task(self.async_start_timer())

    @property
    def hass(self):
        return self._hass

    @property
    def name(self):
        return self._name

    @property
    def domain(self):
        return self._domain

    @property
    def config(self):
        return self._config

    @property
    def update_status_interval(self):
        return self._update_status_interval

    async def async_start_timer(self):

        # This is used to update the status periodically
        self.info(self.name + ' credit will be updated each ' + str(self.update_status_interval))

        # Do not put "self.async_update_credits()", with the parenthesis,
        # otherwise you will pass a Coroutine, not a Coroutine function!
        # and get "Coroutine not allowed to be passed to HassJob"
        # Put "self.async_update_credits" without the parenthesis
        async_track_time_interval(
            self.hass,
            self.async_update_credits,
            self.update_status_interval
        )

    # Do not remove now=None, since when async_track_time_interval()
    # calls async_update_credits(), it passes to the function the time!
    async def async_update_credits(self, now=None):

        self.debug('Updating ' + self._name + ' account credit...')

        threads = []

        for phone_number in self.config[self.domain][CONF_PHONE_NUMBERS]:
            thread = Thread(
                target=self.get_phone_number_credit,
                args=phone_number
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def debug(self, msg):
        _LOGGER.error(msg)

    def info(self, msg):
        _LOGGER.info(msg)

    def error(self, msg):
        _LOGGER.error(msg)

    def save_info(self, pnk, v, attributes):
        self.hass.states.async_set(self.domain + "." + pnk, v['value'], attributes)
