# NFC Secret Issuer

Will eventually pass a url and token that holds a secret.


See [link](https://learn.adafruit.com/adafruit-nfc-rfid-on-raspberry-pi) for tutorial

LibNFC only support UART on PN532. Set

## Wiring for breakout board
Sel0 and Sel1 jumpers on PN532 to L to boot into UART

| RPI  | PN532 |
|---|---|
|5v | 5v |
|GND|GND|
|GPIO14 (TXD0) | RX |
|GPIO15 (RDX0) | TX |

For now:

* Connect PN532 to rpi via serial port & configure serial port
* Build nfclib on rpi