# Procedència i límits de la reconstrucció

## Fitxer de referència verificat

- Nom: Connector_Microbit-ThingSpeak-Serial_v5.1.4.exe
- Versió indicada: **5.1.4**
- SHA-256 de l'executable: **45c5851529ae95736d7551073213bf5576a1534ca7ce7a2cff714de89f9c4ae4**
- Empaquetat amb PyInstaller i CPython 3.12.
- Nom del mòdul principal al CArchive: microbit_thingspeak_gateway.
- SHA-256 del mòdul compilat sense capçalera .pyc: **12a22c48905212d6bf0701333e45695690cbbecd8518777933393f58ac72e7c2**.

El bytecode conté funcions per detectar el port sèrie, llegir i desar AppData, enviar dades a ThingSpeak i mostrar la interfície **Debug** i **Quant a**.

## Distincions importants

**Verificat al binari:** constants i textos de la UI, versió 5.1.4, estructura dels mètodes, destinació HTTPS, flux de configuració i tractament de respostes.

**Reconstruït manualment:** el fitxer font Python d'aquest repositori. El bytecode no conserva els comentaris ni el format originals; aquesta versió s'ha fet a partir del desassemblatge i de les funcions observades, sense afirmar que sigui una recuperació literal de l'antic .py.

**Canvi deliberat:** el logotip institucional incrustat al binari original no s'ha redistribuït. Per a la reconstrucció s'utilitza una icona alternativa.

**Pendent de comprovació:** equivalència completa amb l'EXE històric, validació física amb micro:bit i ThingSpeak, i compilació bit a bit idèntica.

## Sobre la signatura

Els binaris signats amb SignPath han de construir-se a partir d'un commit públic verificable; **no** es pot afirmar que l'EXE històric prové d'aquesta reconstrucció. La signatura d'un EXE i la certificació d'un MSIX per Microsoft Store són procediments diferents.

## Llicència i autories

L'EXE indica llicència **EUPL 1.2** i el copyright **© 2026 Generalitat de Catalunya · Departament d’Educació i Formació Professional**. També identifica **Ignasi Sánchez Rodríguez** com a desenvolupador, dins del projecte **Estació Meteorològica en Xarxa**, **Mentoria 4.0**.

El codi reconstruït inclou el mateix reconeixement. La titularitat i els permisos de marques i logotips institucionals requereixen un tractament separat.
