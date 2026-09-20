# Atelier NEXUS pour Chat — prototype transversal

État : candidat de contrôle isolé, SANDBOX_ONLY. Ce paquet ne protège pas encore le développement réel de NEXUS. Il ne construit ni ne livre d’APK, ne modifie pas la Roadmap et ne possède aucun accès GitHub, Drive, Apps Script ou Lenovo.

## Objectif et périmètre

Le même moteur reçoit des commandes pour les 47 chantiers recensés dans le snapshot de Roadmap : V-001 à V-010, U-001 à U-013, M-001 à M-024. Les futurs identifiants sont refusés tant qu’un opérateur n’a pas ajouté leur configuration. Aucune règle Android n’est codée en dur.

La couverture du routage et des contrôles génériques ne signifie pas que les tests fonctionnels propres aux 47 chantiers ont été exécutés. Les cas de démonstration utilisent exclusivement des fichiers SYNTHETIC. Le statut CLOSED reste protégé : une demande ne le rouvre pas.

## Fonctionnement

POST /v1/commands reçoit six chaînes : request_id, action, workstream_id, target_id, candidate_sha256, authority_revision. Le contrat exact est command.schema.json. Les champs supplémentaires, les clés JSON dupliquées, les commandes libres et les substitutions de types sont refusés. Le validateur Python applique le sous-ensemble fermé utilisé dans ce contrat ; ce n’est pas un validateur JSON Schema général.

Le rôle vient d’un jeton configuré par l’opérateur. L’agent ne peut ni le choisir dans le JSON ni fournir un champ approved ou des résultats de tests. Deux jetons différents sont requis : agent et reviewer. Le jeton reviewer ne doit jamais être remis au modèle ou au connecteur agent.

Les chemins, hashes attendus, composants, dépendances et exigences de preuve viennent exclusivement de la configuration opérateur. Le service relit les octets, contrôle la fermeture des dépendances, le contenu des preuves et leur correspondance au candidat/chantier. Un JSON PASS correctement formé n’est PAS une preuve d’authenticité : les collecteurs indépendants de preuves réelles restent à intégrer.

OPA évalue la politique sandbox. Moteur absent, en erreur ou résultat ambigu : refus. La machine à états locale admet DRAFT → CHECKED (agent) → APPROVED (reviewer) → RELEASED (agent). RELEASED signifie uniquement transition d’une simulation SQLite ; aucun artefact n’est publié. Le plafond de l’adaptateur interdit toujours le mode production et toute suppression.

SQLite regroupe transition, reçu et journal dans une transaction. Les doublons renvoient un reçu HISTORIQUE avec allowed=false, pas une nouvelle permission. Les collisions sont refusées. Un changement de configuration pertinente ou de politique invalide l’acceptation précédente. Les octets sont revérifiés à chaque nouvelle opération.

## Exécution locale

Python 3.11+ et OPA 1.20.2. Aucune dépendance Python supplémentaire. La CI vérifie le hash OPA déjà épinglé dans le workflow OPA existant.

```sh
python3 -m atelier.demo /chemin/prive/nexus-demo
python3 -m atelier.gateway --config /chemin/prive/nexus-demo/operator-config.json --database /chemin/prive/nexus-demo/state.sqlite --opa /chemin/opa
```

La démonstration par défaut permet l’inspection et interdit les transitions. Pour éprouver les transitions sur des données artificielles uniquement : ajouter --synthetic-open lors de la création de la démonstration. Cela ne rouvre aucun chantier NEXUS réel.

```sh
OPA_BIN=/chemin/opa REQUIRE_OPA=1 python3 run_tests.py
```

Sans OPA, les tests d’intégration sont explicitement sautés localement. La CI interdit cette omission. Le fichier test-results.json indique le nombre exact de tests exécutés, échoués et sautés, et maintient production_verified=false et chatgpt_roundtrip_verified=false.

## Connexion depuis Chat

L’interface HTTP et le contrat OpenAPI sont fournis. Le service écoute uniquement sur 127.0.0.1. Aucun connecteur ChatGPT n’est installé et aucune URL publique n’est créée. Un cycle HTTP local est testé ; il ne vaut pas un aller-retour ChatGPT.

La connexion réelle nécessite un hébergement choisi, TLS, authentification, limitation du trafic, un compte de service distinct et un connecteur compatible effectivement disponible dans le compte Chat utilisé. L’agent devrait recevoir seulement l’accès à /v1/commands avec son jeton agent. Son accès direct aux ressources protégées devrait être retiré ou limité. Ce paquet ne modifie aucun droit existant.

## Relation avec NEXUS existant

Source de gouvernance consultée : NEXUS_PROJECT_CONTROL_LIVE, ID 1mVgrCFCWGK8LwxKHMv7VE2UoFX9c1lI4o_UGp8iadFQ. Le snapshot embarqué n’est pas une autorité live. Sa date d’expiration en démonstration est une simulation de fraîcheur, pas un mécanisme de synchronisation Drive.

Base de code : branche nexus-opa-shadow-001, commit 4c0ccd2ee337c721d1f15a1e3f82891f1e56b98d. Le contrôle golden_guard.py et OPA SHADOW_ONLY restent inchangés. Cette politique sandbox utilise un autre package Rego et ne peut promouvoir la politique OPA existante.

## Limites de sécurité et de preuve

- L’opérateur, la configuration, le binaire OPA, la politique et le compte serveur sont de confiance. Un administrateur système peut contourner cette démonstration.
- Le journal détecte une modification interne et interdit UPDATE/DELETE ordinaires ; il n’est pas inviolable face à un administrateur qui réécrit toute la base ou tronque sa fin. Un ancrage externe manque.
- Les lectures de fichiers n’offrent pas une isolation contre un processus local malveillant concurrent. Une installation réelle exige des fichiers immuables et des comptes séparés.
- La transaction couvre seulement SQLite. Les opérations distantes devront employer une file transactionnelle, des identifiants idempotents, des reçus vérifiés et une réconciliation après panne.
- L’authentification de démonstration ne constitue pas une infrastructure de gestion des identités de production.
- Aucun contrôle global de NEXUS, aucune validation fonctionnelle des produits ni aucune release ne sont revendiqués.

Voir docs/COUVERTURE.md et docs/REPRISE.md pour les étapes restantes.
