# Seguretat

## Gestió de la Write API Key

El programa desa localment la Write API Key en un fitxer JSON a AppData o a la ubicació portable. **El fitxer no està xifrat.** No el comparteixis ni el publiquis.

Si detectes una filtració de clau, revoca-la o regenera-la a ThingSpeak i introdueix-ne una de nova a l'aplicació.

## Dades dels sensors

Les dades s'envien directament per HTTPS a l'API oficial de ThingSpeak. No enviïs dades personals, credencials ni localitzacions identificatives de menors.

## Publicació de codi

No publiquis fitxers locals de configuració, claus API, instal·ladors obtinguts de tercers, tokens, configuracions de dispositius privats ni captures que mostrin dades sensibles.

## Incidències de seguretat

Per notificar un problema sensible, contacta amb els mantenidors del repositori per un canal privat en lloc de publicar secrets en un issue públic. La reconstrucció encara no ha estat auditada completament.
