import datetime
from datetime import timedelta
import logging

import requests
import voluptuous as vol

from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from bs4 import BeautifulSoup

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
        vol.Required(CONF_USERNAME): cv.string,

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
# ILIAD PLATFORM
#
# ----------------------------------------------------------------------------------------------------------------------


class HoMobilePlatform:

    def __init__(self, hass, config):

        self._hass = hass
        self._config = config

        self._username = config[DOMAIN][CONF_USERNAME]
        self._password = config[DOMAIN][CONF_PASSWORD]
        self.update_status_interval = config[DOMAIN][CONF_SCAN_INTERVAL]

        self._credit = {
            'voice': {'value': 0, 'icon': 'mdi:phone', 'uom': 's'},
            'voice_max': {'value': None, 'icon': 'mdi:phone', 'uom': 's'},
            'sms': {'value': 0, 'icon': 'mdi:message-text', 'uom': 'SMS'},
            'sms_max': {'value': None, 'icon': 'mdi:message-text', 'uom': 'SMS'},
            'mms': {'value': 0, 'icon': 'mdi:message-image', 'uom': 'MMS'},
            'mms_max': {'value': None, 'icon': 'mdi:message-image', 'uom': 'MMS'},
            'data': {'value': 0, 'icon': 'mdi:web', 'uom': 'GB'},
            'data_max': {'value': None, 'icon': 'mdi:web', 'uom': 'GB'},
            'renewal': {'value': None, 'icon': 'mdi:clock-outline', 'uom': ''},
        }

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

        # login url
        url = 'https://www.ho-mobile.it/leanfe/restAPI/LoginService/checkAccount'

        # enable coockie
        session.post(url)

        # set POST https params
        params = {"email":null,"phoneNumber":self._username,"channel":"WEB"}

        # get response to POST request
        response = session.post(url, params=params)
        # get http status code
        http_status_code = response.status_code
        # check response is okay
        if http_status_code != 200:

            _LOGGER.error('login page (' + url + ') error: ' + str(http_status_code))

        else:
            # get html in bytes
            content = response.content
            _LOGGER.debug(response.text)
            # generate soup object
            soup = BeautifulSoup(content, 'html.parser')
            # end offerta
            div_class = "end_offerta"
            divs = soup.findAll("div", {"class": div_class})
            _LOGGER.debug('Found ' + str(len(divs)) + ' divs having class ' + div_class)
            if len(divs) == 1:
                renewal_str = divs[0].text.strip()
                renewal_datetime = HoMobilePlatform._get_renewal_datetime_from_str(renewal_str)
                self._credit['renewal']['value'] = renewal_datetime
                _LOGGER.info('HoMobile account renewal: '+str(renewal_datetime))
            # find div tags having class conso__text
            div_class = "conso__text"
            divs = soup.findAll("div", {"class": div_class})
            _LOGGER.debug('Found '+str(len(divs))+' divs having class '+div_class)
            for div in divs:
                # find span tags having class red
                span_class = "red"
                spans = div.findAll("span", {"class": span_class})
                _LOGGER.debug('Found ' + str(len(spans)) + ' spans having class ' + span_class)
                for span in spans:
                    text = span.text
                    if text[-1:] == 's':
                        # voice seconds
                        self._credit['voice']['value'] = int(text[:-1])
                        max = HoMobilePlatform._get_max(div)
                        if max is not None:
                            self._credit['voice_max']['value'] = int(max[:-1])
                    elif text[-2:] == 'GB':
                        # GB of data
                        GB = text[:-2].replace(',', '.')
                        self._credit['data']['value'] = float(GB)
                        max = HoMobilePlatform._get_max(div)
                        if max is not None:
                            self._credit['data_max']['value'] = float(max[:-2].replace(',', '.'))
                    elif text[-3:] == 'SMS':
                        # sms
                        self._credit['sms']['value'] = int(text[:-3].strip())
                        max = HoMobilePlatform._get_max(div)
                        if max is not None:
                            self._credit['sms_max']['value'] = int(max[:-3].strip())
                    elif text[-3:] == 'MMS':
                        # sms
                        self._credit['mms']['value'] = int(text[:-3].strip())
                        max = HoMobilePlatform._get_max(div)
                        if max is not None:
                            self._credit['mms_max']['value'] = int(max[:-3].strip())

            for k, v in self._credit.items():
                if v['value'] is not None:
                    _LOGGER.info(k+': '+str(v['value']))
                    attributes = {"icon": v['icon'], 'unit_of_measurement': v['uom']}
                    self._hass.states.async_set(DOMAIN + "." + OBJECT_ID_CREDIT + "_" + k, v['value'], attributes)
            return True

        return False
