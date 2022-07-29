# hassio_ho.mobile_account

Installazione:
- Creare la directory "custom_components" nella directory principale (quella che contiene il file configuration.yaml)
- Nella directory "custom_components", creare la directory "ho_mobile_account"
- Nella directory "ho_mobile_account" copia i file "___init.py___" e "manifest.json"
- Riavviare Home Assistant
- Dopo aver riavviato Home Assistant, nel file "configuration.yaml" aggiungere le seguenti righe (e salvare):
ho_mobile_account: 
  phone_number: !secret ho_mobile_account_phone_number
  password: !secret ho_mobile_account_password
- Andare nel file "secrets.yaml" e aggiungere le seguenti righe (e salvare):
ho_mobile_account_phone_number: "inserire-qui-il-numero-di-teleno"
ho_mobile_account_password: "inserire-qui-la-password"
- Riavviare Home Assistant
- Dovrebbero comparirè le seguenti entità:
ho_mobile_account.internet > GB rimasti
ho_mobile_account.internet_renewal > Data del prossimo rinnovo
ho_mobile_account.internet_threshold > GB totali della offerta


