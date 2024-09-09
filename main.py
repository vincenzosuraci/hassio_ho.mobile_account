from ho_mobile import HoMobile
from vodafone import Vodafone

# ----------------------------------------------------------------------------------------------------------------------
#
# MAIN
#
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # ------------------------------------------------------------------------------------------------------------------
    # Ho.Mobile
    # ------------------------------------------------------------------------------------------------------------------

    phone_numbers = [ ]
    password = "xxx"

    ho_mobile = HoMobile(phone_numbers, password)

    for phone_number in phone_numbers:
        ho_mobile.get_phone_number_credit(phone_number, password)

    # ------------------------------------------------------------------------------------------------------------------
    # Vodafone
    # ------------------------------------------------------------------------------------------------------------------

    phone_numbers = [ "xxx", "yyy" ]
    password = "xxx"

    vodafone = Vodafone(phone_numbers, password)

    for phone_number in phone_numbers:
        vodafone.get_phone_number_credit(phone_number, password)