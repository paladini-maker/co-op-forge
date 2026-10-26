# Flujo recomendado: GLB → Blender → SMD/QC → Sven Co-op

1. **Inspeccionar el original.** Mantenga una copia del GLB original y compruebe escala, eje vertical, transformaciones, materiales, armature y animaciones.
2. **Importar en Co-Op Forge.** Utilice la vista previa y el informe de compatibilidad. Las advertencias no deben tratarse como una certificación.
3. **Abrir Blender.** Importe el GLB original en Blender para conservar el modelo fuente. La app genera un JSON de setup; el puente Python construye una armature de bloque a partir de los marcadores 2D. Compruebe escala, profundidad, nombres y ubicación de cada hueso.
4. **Peso y retargeting.** Las asignaciones rígidas aproximadas sólo son un punto de partida. Corrija pesos, orden de huesos, pose de bind, root, nombres y animaciones. No use el rig genérico como reemplazo automático del esqueleto de un jugador existente.
5. **Exportar SMD/QC.** Emplee un exportador compatible y revise en los SMD el material asignado a cada triángulo, UV, normales, jerarquía y bone weights. Adapte el QC a las secuencias reales y directivas admitidas por la versión de StudioMDL.
6. **Compilar y probar.** Compile con la herramienta StudioMDL adecuada al objetivo GoldSrc/Sven Co-op. Revise mensajes del compilador, abra el MDL en un visor y pruebe en una instalación de prueba del juego.
7. **Iterar con cambios pequeños.** Mantenga QC, SMD, texturas y log del compilador en el proyecto local. Pruebe los límites del compilador concreto; los valores de otras versiones no son garantía.

## No prometido por este prototipo

- Conservación perfecta de la jerarquía, pesos o animaciones del GLB original.
- Conversión automática sin pérdidas de materiales/texturas a formatos GoldSrc.
- Compilación de MDL desde el navegador.
- Compatibilidad garantizada con todas las versiones de GoldSrc, Half-Life o Sven Co-op.
