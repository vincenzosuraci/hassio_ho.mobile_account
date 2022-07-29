import datetime
from datetime import timedelta
import logging

import requests
import voluptuous as vol

from homeassistant.const import (CONF_PHONE_NUMBER, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from bs4 import BeautifulSoup

import json as JSON

# Setting log
_LOGGER = logging.getLogger('ho_mobile_account_init')
_LOGGER.setLevel(logging.DEBUG)

# This is needed, it impact on the name to be called in configurations.yaml
# Ref: https://developers.home-assistant.io/docs/en/creating_integration_manifest.html
DOMAIN = 'ho_mobile_account'

REQUIREMENTS = ['beautifulsoup4']

OBJECT_ID_CREDIT = 'credit'

DEFAULT_SCAN_INTERVAL = timedelta(seconds=900)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_PHONE_NUMBER): cv.string,

        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)


# ----------------------------------------------------------------------------------------------------------------------
#
# ASYNC SETUP
#
# ----------------------------------------------------------------------------------------------------------------------


async def async_setup(hass, config):

    _LOGGER.debug('async_setup() >>> STARTED')

    # create the HoMobile Platform object
    hass.data[DOMAIN] = HoMobilePlatform(hass, config)

    _LOGGER.debug('async_setup() <<< TERMINATED')

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

        self._phoneNumber = config[DOMAIN][CONF_PHONE_NUMBER]
        self._password = config[DOMAIN][CONF_PASSWORD]
        self.update_status_interval = config[DOMAIN][CONF_SCAN_INTERVAL]

        self._credit = {}

        # login and fetch data
        hass.async_create_task(self.async_update_credits())

        # starting timers
        hass.async_create_task(self.async_start_timer())

    async def async_start_timer(self):

        # This is used to update the Meross Devices status periodically
        _LOGGER.info('HoMobile credit will be updated each ' + str(self.update_status_interval))
        async_track_time_interval(self._hass,
                                  self.async_update_credits,
                                  self.update_status_interval)

        return True

    @staticmethod
    def _get_max(elem):
        for content in elem.contents:
            content = str(content).strip()
            if content[:1] == '/':
                return content[1:].strip()
        return None

    @staticmethod
    def _get_renewal_datetime_from_str(renewal_str):
        index = renewal_str.find(':')
        _LOGGER.debug('looking for ":", index: ' + str(index))
        if index >= 0:
            H = int(renewal_str[index-2:index])
            i = int(renewal_str[index+1:index+3])
            _LOGGER.debug('time: ' + str(H) + ':' + str(i))
            index = renewal_str.find('/')
            _LOGGER.debug('looking for "/", index: ' + str(index))
            if index >= 0:
                d = int(renewal_str[index-2:index])
                m = int(renewal_str[index+1:index+3])
                Y = int(renewal_str[index+4:index+8])
                _LOGGER.debug('date: ' + str(d) + '/' + str(m) + '/' + str(Y))
                dt = datetime.datetime.combine(datetime.date(Y, m, d), datetime.time(H, i))
                _LOGGER.info('renewal datetime: ' + str(dt))
                return dt

        return renewal_str

    async def async_update_credits(self, now=None):

        # Session keeping cookies
        session = requests.Session()

        _LOGGER.debug('Updating HoMobile account credit...')

        # --------------------------------------------------------------------------------------------------------------
        #   FASE 1 - Caricamento della homepage
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'https://www.ho-mobile.it/'

        # enable coockie
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
            #   FASE 2 - Inserimento del numero di telefono
            # ----------------------------------------------------------------------------------------------------------

            # login url
            url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

            # set POST https params
            json = {
                'email': None,
                'phoneNumber':self._phoneNumber,
                'channel':'WEB'
            }
            headers = {
                'Referer':'https://www.ho-mobile.it/',
                'Content-Type':'application/json'
            }

            # get response to POST request
            response = session.post(url, json=json, headers=headers)
            # get http status code
            http_status_code = response.status_code
            # check response is okay
            if http_status_code != 200:

                _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                # get html in bytes
                _LOGGER.debug(str(response.content))

            else:
                # get html in bytes
                json_str = response.text
                #_LOGGER.debug(json_str)
                json = JSON.loads(json_str)
                #_LOGGER.debug(str(json))
                _LOGGER.debug('Status is ' + json['operationStatus']['status'])

                if json['operationStatus']['status'] == 'OK':

                    # --------------------------------------------------------------------------------------------------
                    #   FASE 2 - Inserimento della password
                    # --------------------------------------------------------------------------------------------------

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

                    # get response to POST request
                    response = session.post(url, json=json, headers=headers)

                    # get http status code
                    http_status_code = response.status_code

                    # check response is okay
                    if http_status_code != 200:

                        _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                        # get html in bytes
                        _LOGGER.debug(str(response.content))

                    else:
                        # get html in bytes
                        _LOGGER.debug('Username e password inseriti CORRETTAMENTE')

                        # --------------------------------------------------------------------------------------------------
                        #   FASE 3 - Recupero del productId
                        # --------------------------------------------------------------------------------------------------

                        # login url
                        url = 'https://www.ho-mobile.it/leanfe/restAPI/CatalogInfoactivationService/getCatalogInfoactivation'

                        # set POST https params
                        json = {
                            "channel":"WEB",
                            "phoneNumber":self._phoneNumber
                        }

                        headers = {
                            'Referer': 'https://www.ho-mobile.it/',
                            'Content-Type': 'application/json'
                        }

                        # get response to POST request
                        response = session.post(url, json=json, headers=headers)

                        # get http status code
                        http_status_code = response.status_code

                        # check response is okay
                        if http_status_code != 200:

                            _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                            # get html in bytes
                            _LOGGER.debug(str(response.content))

                        else:

                            json_str = response.text
                            #_LOGGER.debug(json_str)
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

                            # get response to POST request
                            response = session.post(url, json=json, headers=headers)

                            # get http status code
                            http_status_code = response.status_code

                            # check response is okay
                            if http_status_code != 200:

                                _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

                                # get html in bytes
                                _LOGGER.debug(str(response.content))

                            else:

                                json_str = response.text
                                #_LOGGER.debug(json_str)

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
                                        attributes = {"icon": v['icon'], 'unit_of_measurement': v['uom']}
                                        self._hass.states.async_set(DOMAIN + "." + k, v['value'], attributes)
                                return True

        return False
