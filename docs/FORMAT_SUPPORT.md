# Formatos y límites conocidos

| Entrada | Soporte | Limitación importante |
|---|---|---|
| OBJ | Lectura local de vértices y caras | No transporta rig, pesos, animaciones ni una definición material completa. |
| SMD | Lectura local de geometría, materiales y jerarquía | La generación de rig puede crear una jerarquía nueva; revise nombres y bind pose. |
| GLB 2.0 binario | Parser local de geometría, transforms, primitivas, nodos y datos de skinning que el parser reconoce | Extensiones requeridas desconocidas, compresión, morph targets, texturas y animaciones pueden no transferirse al SMD de salida. Use GLB autocontenido. |
| QC | Inspección y QC inicial | Las secuencias, hitboxes, skin references, flags y directivas son específicas del modelo/compilador y deben comprobarse. |
| GLTF con buffers externos / FBX | No parseado directamente en esta versión | Convierta a GLB binario autocontenido, OBJ o SMD con un programa de modelado. |
| MDL binario | No se decompila en el navegador | Use una herramienta compatible para recuperar SMD/QC. |

La salida SMD generada es una base de conversión, no una conversión sin pérdidas. El flujo de GoldSrc clásico suele emplear un vértice rígidamente asignado a un hueso, mientras que glTF admite influencias múltiples. Pesos, materiales, textura/paleta, secuencias, root motion, nombres de huesos, hitboxes y límites del compilador requieren verificación. La aplicación no certifica compatibilidad universal ni compila un `.mdl`.
