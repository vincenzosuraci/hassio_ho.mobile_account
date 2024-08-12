import requests

from datetime import datetime

import json as json_lib

# ----------------------------------------------------------------------------------------------------------------------
#
# HO.MOBILE PLATFORM
#
# ----------------------------------------------------------------------------------------------------------------------


class HoMobile:

    def __init__(self, phone_numbers, password):
        self._phone_numbers = phone_numbers
        self._password = password
        self._credit = {}

    @property
    def phone_numbers(self):
        return self._phone_numbers

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
                                    if uom in ['GB','MB']:

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
