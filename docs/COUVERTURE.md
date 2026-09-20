# Couverture du prototype

| Incident de l’audit | Contrôle fourni | Portée démontrable |
|---|---|---|
| Exécution assimilée à acceptation | Rôles séparés et transition reviewer | Commandes HTTP/locales sandbox |
| Mauvaise cible | Association chantier + cible configurée | Registre opérateur artificiel |
| CURRENT contradictoire ou périmé | Révision et expiration, drapeau de conflit | Données opérateur ; synchronisation live à construire |
| Ancien PASS utilisé pour une autre version | Hash candidat + identité chantier dans preuve brute | Structure et octets, pas authenticité de l’émetteur |
| TECH PASS assimilé à REAL PASS | Types de preuves distincts requis | Fixtures TECH et REAL |
| Dépendance oubliée | Fermeture transitive, cycles, BOM, hashes | Composants déclarés ; inventaire réel à réconcilier |
| Nettoyage dangereux | Suppression toujours refusée | Aucun chemin de suppression exposé |
| Collision ou répétition | Transaction et request_id unique | SQLite ; pas encore opérations distantes |
| Perte après interruption | Reprise depuis SQLite | Test de recréation du service |
| Perte de journal | Append-only et contrôle de chaîne | Pas de garantie contre administrateur |
| Régression fonctionnelle | Contrat de preuve requis | Les comportements NEXUS eux-mêmes ne sont pas testés ici |

## Trois niveaux distincts

1. Identifiants couverts : 47 présents dans le snapshot, extensible par configuration explicite.
2. Contrôles génériques testés : suite du prototype, données artificielles.
3. Protections NEXUS actives : NON. Aucun droit ni exécuteur réel raccordé.

Le corpus utilise une configuration SYNTHETIC_OPEN pour exercer les transitions de chaque identifiant. Cette configuration ne constitue jamais une réouverture ou autorisation des chantiers CURRENT.
