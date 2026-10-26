# Co-Op Forge — Sven Co-op Player Rig Studio

Herramienta web local para inspeccionar geometría de modelos, ajustar marcadores humanoides y preparar archivos de referencia para un flujo Blender → SMD/QC → GoldSrc/Sven Co-op.

> **Estado:** prototipo funcional, no un compilador de modelos. La app genera un SMD de referencia con asignaciones rígidas aproximadas y un QC inicial. No certifica un `.mdl` jugable ni preserva automáticamente el rig o las animaciones originales.

## Inicio rápido

1. Descarga o clona este repositorio.
2. Abre `index.html` en un navegador moderno (Chrome, Edge o Firefox reciente). No hay build frontend ni dependencias de servidor.
3. Importa un OBJ, SMD o GLB binario autocontenido; la lectura se realiza localmente en el navegador.
4. Ajusta los marcadores y la referencia visual.
5. En **Pipeline integrado**, ejecuta la validación y descarga el paquete ZIP de proyecto.
6. Si vas a usar Blender, importa la malla allí y ejecuta `tools/co_op_forge_blender_bridge.py` o descarga la copia embebida desde la propia app.
7. Revisa SMD/QC, secuencias, materiales, hitboxes, orientación y escala. Compila con un `studiomdl` compatible con tu versión de Sven Co-op y prueba el resultado dentro del juego.

## Formatos

| Formato | Estado en esta versión | Notas |
|---|---|---|
| OBJ | Lectura de geometría | No aporta esqueleto ni pesos; el rigger asigna pesos rígidos aproximados. |
| SMD | Lectura de geometría, materiales y jerarquía | La salida generada usa un esqueleto nuevo; no es una edición fiel del rig original. |
| GLB 2.0 binario | Lectura de geometría y datos de skinning compatibles | No preserva todas las extensiones, animaciones, morph targets o materiales en la salida GoldSrc. Se requiere GLB autocontenido. |
| QC | Inspección de directivas y plantilla inicial | QC generado es un andamio: hay que adaptar secuencias, hitboxes y referencias a archivos reales. |
| GLTF externo / FBX | No parseado directamente | Convierte a GLB autocontenido u OBJ/SMD con una herramienta de modelado. |
| MDL binario | No decodificado por la app | Usa un decompilador/herramienta compatible y trabaja con sus SMD/QC. |

La importación estructural no equivale a interoperabilidad perfecta. En el formato de salida de GoldSrc deben revisarse los materiales/texturas, nombres de hueso, escala, ejes, límites del compilador y secuencias de animación.

## Integración con GitHub

Consulta [`docs/GITHUB_INTEGRATION.md`](docs/GITHUB_INTEGRATION.md) para crear o conectar el repositorio remoto y publicar la app. El paquete preparado no ha sido enviado a una cuenta GitHub.

## GitHub Pages

El workflow `.github/workflows/pages.yml` publica solo `index.html` al hacer push a `main` o al ejecutarse manualmente.

1. Sube el contenido del repositorio a GitHub.
2. En **Settings → Pages**, selecciona **GitHub Actions** como fuente de despliegue si no se seleccionó automáticamente.
3. Revisa **Actions** para ver el resultado. La URL se mostrará en el resumen del job de Pages.

## Pruebas locales

Requisitos para validación: Python 3.10+ y Node.js 20+. La aplicación web en sí no requiere estas herramientas.

```bash
python scripts/validate_project.py
python -m unittest discover -s tests -v
```

## Estructura

```text
index.html                           Aplicación web estática, sin build
tools/co_op_forge_blender_bridge.py  Puente opcional para Blender
docs/FORMAT_SUPPORT.md               Formatos, capacidades y pérdidas
docs/GOLDSRC_PIPELINE.md             Flujo de producción GoldSrc
tests/                               Pruebas de estructura y regresión
scripts/validate_project.py          Validación estática y sintaxis
.github/workflows/                   CI y GitHub Pages
```

## Privacidad

El procesamiento de modelos y referencias es local en el navegador. GitHub Pages sirve el archivo estático; no hay backend de subida de modelos ni telemetría añadida por este proyecto. Si publicas archivos de prueba en el repositorio, recuerda que un repositorio público hace que esos archivos sean públicos.

## Licencia

Distribuido bajo la licencia MIT; consulta `LICENSE`. Las herramientas externas enlazadas mantienen sus respectivas licencias y condiciones.
