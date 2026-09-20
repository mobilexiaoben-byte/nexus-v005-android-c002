# Reprise et passage à une utilisation réelle

Le livrable de cette étape est un prototype testable et versionné. La demande couvre tous les chantiers, pas seulement Android.

Ordre des dépendances pour l’étape suivante :

1. Relire la Roadmap et ACTION_POLICY. Maintenir OPA existant SHADOW_ONLY jusqu’aux gates prévues.
2. Identifier l’hébergement de l’atelier et le mécanisme de connexion réellement utilisable depuis Chat. Ne pas inventer de service ou de compte.
3. Créer une identité d’exécution distincte ; retirer aux clients les chemins d’écriture contournant l’atelier. Ne pas retirer l’accès de secours du propriétaire.
4. Protéger le code de contrôle et ses tests dans un périmètre indépendant des correctifs proposés par l’agent. Configurer les contrôles GitHub obligatoires après validation explicite des règles.
5. Relier des lectures authentifiées de CURRENT, des preuves CI, des artefacts et registres. Vérifier la provenance avant d’autoriser une opération.
6. Implémenter un adaptateur réel à la fois, avec simulation, identité stable, idempotence, réconciliation après panne et restauration. Aucun passage implicite à production.
7. Rejouer les incidents de l’audit contre chaque chemin réellement exposé. Vérifier les accès de contournement, les révocations et les échecs du moteur de contrôle.
8. Effectuer un aller-retour réel depuis Chat avant de déclarer la connexion opérationnelle.

L’activation globale ne doit pas être déduite d’un succès CI du prototype. GitHub Rulesets, comptes de service, connecteur Chat, hébergement et collecteurs de preuves ne sont pas installés par ce paquet.

## Écart observé pendant cette exécution

La branche nexus-opa-shadow-001 a avancé de 4c0ccd2ee337c721d1f15a1e3f82891f1e56b98d à 418ffbed4267df21b95ad0f96bbd439c58421dc3 pendant le travail. Le diff ajoute dual_guard.py et des appels DUAL_ENFORCEMENT dans deux workflows. ACTION_POLICY relue à cette étape indique encore SHADOW_ONLY. Aucune conclusion sur l’autorisation de cette autre intervention n’est tirée. Le prototype est dérivé du commit figé 4c0ccd2ee337c721d1f15a1e3f82891f1e56b98d, sans modifier cette branche ni main. Réconciliation obligatoire avant activation réelle.
