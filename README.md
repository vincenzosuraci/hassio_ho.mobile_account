# Introduzione
- Questo custom component permette di recuperare le seguenti informazioni realtive alla scheda SIM dell'operatore <code>ho-mobile</code>: 
  - numero di GB (internet/dati) rimanenti; 
  - numero di GB totali previsti dal piano;
  - data del successivo rinnovo.
- Viene supportato il caso di 2 o più SIM (numeri di telefono) associate allo stesso account (password).
- Non è supportato il caso di 2 o più account.

# Installazione
- Creare la directory <code>custom_components</code> nella directory principale (quella che contiene il file <code>configuration.yaml</code>)
- Nella directory <code>custom_components</code>, creare la directory <code>ho_mobile_account</code>
- Nella directory <code>ho_mobile_account</code> copia i file <code>\_\_init.py\_\_</code> e <code>manifest.json</code>
- Riavviare Home Assistant
- Dopo aver riavviato Home Assistant, nel file <code>configuration.yaml</code> aggiungere le seguenti righe (e salvare):

```yaml
ho_mobile_account:
  phone_numbers: !secret ho_mobile_account_phone_numbers
  password: !secret ho_mobile_account_password
  ```

- Andare nel file <code>secrets.yaml</code> e aggiungere le seguenti righe (e salvare):

```yaml
ho_mobile_account_password: "inserire-qui-la-password"
ho_mobile_account_phone_numbers: 
  - "inserire-qui-il-numero-di-telefono-#1"
  - "inserire-qui-il-numero-di-telefono-#2"  
```

- Riavviare Home Assistant
- Dovrebbero comparire le seguenti terne di entità (una terna per ogni numero di telefono):
  - <code>ho_mobile_account.\<numero-di-telefono\>_internet</code> > GB rimasti
  - <code>ho_mobile_account.\<numero-di-telefono\>_internet_renewal</code> > Data del prossimo rinnovo
  - <code>ho_mobile_account.\<numero-di-telefono\>_internet_threshold</code> > GB totali della offerta

# Configurazione
- Di default, viene eseguito un aggiornamento dei dati ogni 15 minuti
- Si può personalizzare il periodo di aggiornamento dei dati, configurando il paramentro <code>scan_interval</code> espresso in secondi:
```yaml
ho_mobile_account:
  phone_numbers: !secret ho_mobile_account_phone_numbers
  password: !secret ho_mobile_account_password
  scan_interval: 900
  ```

