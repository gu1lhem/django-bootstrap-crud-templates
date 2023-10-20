# BSCT - Django Bootstrap CRUD Templates

BSCT est une bibliothèque de templates pour Django qui permet de créer des pages CRUD (Create, Read, Update, Delete) avec Bootstrap. Elle permet de créer des pages CRUD avec Bootstrap sans utiliser de templates. On ne redéfinit que les blocks que l'on veut modifier.

Voir le fichier `README.rst` ou [le dépôt GitHub](https://github.com/Alem/django-bootstrap-crud-templates) pour plus d'informations.

/!\ Seul le répertoire `bsct` a été modifié. Les autres fichiers sont ceux de la bibliothèque originale et ne sont plus maintenus.

## Installation

- Placer le répertoire `bsct` dans le répertoire principal de votre projet Django.
- Dans le fichier `settings.py` de votre projet, ajouter `bsct` à la liste des applications installées.
- Définir un paramètre `BSCT_LOGGER_NAME` dans le fichier `settings.py` de votre projet. Ce paramètre permet de définir le nom du logger utilisé par BSCT. Par défaut, le logger est `bsct`.
- Placer les fichiers du répertoire `static` dans le répertoire `static` de votre projet Django.
- Définir le paramètre `STATIC_URL` dans le fichier `settings.py` de votre projet. Ce paramètre permet de définir l'URL de base des fichiers statiques. Par défaut, l'URL est `/static/`.

## Redéfinition des templates

Les templates d'un modèle peuvent être redéfinis en créant un répertoire `templates` dans le répertoire principal de votre projet Django. Ce répertoire doit contenir un sous-répertoire `app` avec app le nom de votre application, et un sous-répertoire `model` avec model le nom de votre modèle. Par exemple, pour le modèle `Person` de l'application `peoples`, le répertoire doit être `templates/people/person`. Les templates redéfinis doivent avoir le même nom que les templates de BSCT, c'est-à-dire `create.html`, `detail.html`, `delete.html`, `update.html` et `list.html`. Ils sont détectés au chargement de l'application.

## Redéfinition des vues

Les vues d'un modèle peuvent être redéfinies en créant une classe dans le fichier `views.py` de votre projet Django. 
Par exemple, pour le modèle `Person` si l'on veut redéfinir la vue de création, on créé `PersonCreateView(bsct.views.CreateView)`. Elle serra détectée au chargement de l'application. On pourrait alors redéfinir des méthodes, comme `get_context_data()` pour ajouter du contexte supplémentaire à la vue, par exemple.
Attention : il n'est pas possible de définir l'attribut `fields` dans la classe. Il faut donc créer un `Form` dans `forms.py` et le passer à l'`URLGenerator` de `BSCT` par l'argument l'argument `form_class` ; ou bien redéfinir la méthode `get_allowed_fields()` du modèle.

## Mise à jour

Pour mettre à jour les librairies de [Datatables](https://datatables.net/download/), les télécharger depuis le site de DataTables en sélectionnant les options ci-dessous, puis remplacer les fichiers dans `static/DataTables/`. Le choix est fait de ne pas utiliser de CDNs pour augmenter la résilience et car la bande passante n'est pas limitée.
Les choix actuels pour Datatables sont les suivants :
Styling framework :

- Bootstrap 5

Packages :

- Bootstrap 5
- JQuery 3
- DataTables

Extensions :

- AutoFill
- Buttons
  - Column visibility
  - HTML5 export
    - JSZip
    - pdfmake
- ColReorder
- DateTime
- Select
- StateRestore

Download method : Download, avec les options _Minify_ et _Concatenate_ cochées.

Pour le déploiement, un changement de fichiers dans `app/static/` nécessite de ré-exécuter `python ./manage.py collectstatic`.
