import base64

import requests

from datetime import datetime

import json as json_lib


# ----------------------------------------------------------------------------------------------------------------------
#
# 1NCE CRAWLER
#
# ----------------------------------------------------------------------------------------------------------------------


class Once:

    def __init__(
        self,
        username,
        password
    ):
        self._username = username
        self._password = password
        self._credit = {}

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def sim_iccids(self):
        return self._sim_iccids

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

    def get_sim_credit(self, iccid):

        # --------------------------------------------------------------------------------------------------------------
        #   FASE 1 - Obtain Access Token
        # --------------------------------------------------------------------------------------------------------------

        # login url
        url = 'https://api.1nce.com/management-api/oauth/token'

        # session keeping cookies
        session = requests.Session()

        json = {
            "grant_type": "client_credentials"
        }

        user_pass_str = self.username + ":" + self.password
        base64_user_pass_bytes = base64.b64encode(bytes(user_pass_str, 'utf-8'))
        base64_user_pass_str = base64_user_pass_bytes.decode('utf-8')

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + base64_user_pass_str
        }

        response = requests.post(
            url=url,
            json=json,
            headers=headers
        )

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

            # get html in bytes
            json_str = response.text
            json = json_lib.loads(json_str)
            access_token = json["access_token"]

            url = "https://api.1nce.com/management-api/v1/sims/" + iccid + "/quota/data"

            headers = {
                "accept": "application/json",
                "authorization": "Bearer " + access_token
            }

            response = requests.get(
                url,
                headers=headers
            )

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

                if iccid not in self.credit:
                    self.credit[iccid] = {}

                self.credit[iccid]["volume"] = {
                    "value": json["volume"],
                    "icon": "mdi:web",
                    "uom": "MB"
                }

                self.credit[iccid]["total_volume"] = {
                    "value": json["total_volume"],
                    "icon": "mdi:web",
                    "uom": "MB"
                }

                # Converti la stringa in un oggetto datetime
                exp_date_obj = datetime.strptime(json["expiry_date"], "%Y-%m-%d %H:%M:%S")

                # Converti l'oggetto datetime nel formato desiderato
                exp_date_value = exp_date_obj.strftime("%d-%m-%Y")

                self.credit[iccid]["expiry_date"] = {
                    "value": exp_date_value,
                    "icon": "mdi:calendar-clock",
                    "uom": ""
                }

                for k, v in self.credit[iccid].items():
                    if v['value'] is not None:
                        pnk = iccid + '_' + k
                        self.info(pnk + ': ' + str(v['value']))
                        attributes = {
                            'icon': v['icon'],
                            'unit_of_measurement': v['uom']
                        }
                        self.save_info(pnk, v, attributes)

