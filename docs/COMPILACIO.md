# Compilació Windows de la reconstrucció v5.1.4

**Requisits:** Windows 10/11, Python 3.12 i connexió a Internet per descarregar les dependències. No cal maquinari real per executar les proves automatitzades.

## 1. Instal·lar les dependències

~~~cmd
py -3.12 -m pip install -r requirements.txt -r requirements-build.txt
~~~

## 2. Provar el codi

~~~cmd
py -3.12 -m unittest discover -s tests -v
~~~

Els tests simulen un dispositiu sèrie, l'API HTTP i la configuració. Això no substitueix una prova física amb micro:bit i ThingSpeak.

## 3. Crear un EXE

~~~cmd
build_windows.bat
~~~

L'arxiu generat apareix a la carpeta dist. El nom de sortida acaba en **_rebuild** per distingir-lo de l'EXE històric.

## 4. GitHub Actions

A cada pujada a main o pull request, el workflow compila una còpia **sense signar**. El resultat es descarrega des dels artefactes de la pestanya Actions.

## 5. Signatura de codi i Microsoft Store

El repositori es prepara com a punt de partida per a SignPath Foundation. Abans de sol·licitar signatura, cal comprovar les seves condicions vigents, els drets del codi, la política de revisió dels canvis i la traçabilitat d'un nou build.

El paquet MSIX aprovat o pendent a Microsoft Store és independent d'aquest repositori. **No s'ha de substituir automàticament el binari distribuït per la reconstrucció sense validar-la.**

## 6. Reproduïbilitat i procedència

Els noms i versions de les dependències directes estan fixats. Per assolir una compilació verificable completa caldrà registrar també les dependències transitives, el sistema de build i la revisió exacta de GitHub. No s'afirma que l'EXE generat sigui idèntic byte a byte a la versió històrica.
