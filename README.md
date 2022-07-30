# Introduzione
- Questo custom component permette il recupero delle informazioni sul numero di GB (internet/dati) rimanenti, sui GB totali previsti dal piano e sulla data del successivo rinnovo. 
- Non è attualmente supportato il caso di 2 o più SIM. In particolare, attualmente è supportato il caso di una sola SIM.

# Installazione
- Creare la directory <code>custom_components</code> nella directory principale (quella che contiene il file <code>configuration.yaml</code>)
- Nella directory <code>custom_components</code>, creare la directory <code>ho_mobile_account</code>
- Nella directory <code>ho_mobile_account</code> copia i file <code>\_\_init.py\_\_</code> e <code>manifest.json</code>
- Riavviare Home Assistant
- Dopo aver riavviato Home Assistant, nel file <code>configuration.yaml</code> aggiungere le seguenti righe (e salvare):

```yaml
ho_mobile_account:
  phone_number: !secret ho_mobile_account_phone_number
  password: !secret ho_mobile_account_password
  ```

- Andare nel file "secrets.yaml" e aggiungere le seguenti righe (e salvare):

```yaml
ho_mobile_account_phone_number: "inserire-qui-il-numero-di-telefono"  
ho_mobile_account_password: "inserire-qui-la-password"
```

- Riavviare Home Assistant
- Dovrebbero comparire le seguenti entità:
  - <code>ho_mobile_account.internet</code> > GB rimasti
  - <code>ho_mobile_account.internet_renewal</code> > Data del prossimo rinnovo
  - <code>ho_mobile_account.internet_threshold</code> > GB totali della offerta


