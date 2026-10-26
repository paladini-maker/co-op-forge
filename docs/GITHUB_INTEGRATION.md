# Subir Co-Op Forge a GitHub

Repositorio previsto: <https://github.com/paladini-maker/co-op-forge>

## Opción 1: PowerShell (Windows)

1. Descarga y extrae `co-op-forge-github-ready.zip`.
2. Instala Git for Windows si todavía no está instalado.
3. Abre PowerShell en la carpeta extraída `co-op-forge-github`.
4. Autentícate con Git Credential Manager cuando Git lo solicite, y ejecuta:

```powershell
.\scripts\publish-to-github.ps1
```

El script valida el proyecto y, si esta carpeta todavía no es un clon, clona primero el remoto existente y copia los archivos sobre él para preservar un README inicial u otros commits. Si ya estás dentro de un checkout, exige que `origin` coincida exactamente con el repositorio configurado. Hace un push normal y nunca usa `--force`; si hay ramas divergentes, se detiene para evitar sobrescribir datos.

También puedes ejecutar los comandos manualmente:

```powershell
git init -b main
git add --all
git commit -m "Initial commit: Co-Op Forge"
git remote add origin https://github.com/paladini-maker/co-op-forge.git
git push -u origin main
```

Si el repositorio remoto contiene otros commits o cambios no relacionados, revísalos antes de publicar. El script no fuerza actualizaciones; un rechazo non-fast-forward debe resolverse manualmente.

## Opción 2: GitHub web

Carga los archivos del ZIP mediante la interfaz web de GitHub, conservando las carpetas `.github`, `docs`, `scripts`, `tests` y `tools`. Para un proyecto de este tamaño, Git es preferible a cargar cada archivo individualmente.

## Activar GitHub Pages

1. En el repositorio, abre **Settings → Pages**.
2. En **Build and deployment → Source**, selecciona **GitHub Actions**.
3. Empuja a `main` o ejecuta manualmente `Deploy static app to GitHub Pages` en **Actions**.
4. Revisa el resumen del workflow para ver la URL publicada.

El sitio público contiene únicamente `index.html` y `.nojekyll` dentro de `site/`. Los archivos de desarrollo no se publican en la página.

## Comprobar CI en local

Requisitos: Python 3.10 o más reciente y Node.js 20 o más reciente.

```powershell
python scripts/validate_project.py
python -m unittest discover -s tests -v
```

El runtime de la web no requiere build de Node ni dependencias de Python; Node sólo valida la sintaxis JavaScript en CI.
