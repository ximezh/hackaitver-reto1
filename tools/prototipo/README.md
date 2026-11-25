# Visor del prototipo

Abre las pantallas de `design/CEDIS Flow` en el navegador, tal como las dibuja el prototipo, para compararlas con el front (DoD de front, hallazgo H-16).

```bash
cd tools/prototipo
npm run prototipo          # http://localhost:5180
PUERTO=5181 npm run prototipo
```

- `/` lista las pantallas por grupo, con su tamaño de tarjeta.
- `/c/<Pantalla>` abre una vista previa, por ejemplo `/c/Caseta`.

Inyecta `tokens.css`, `components/bundle.css` y `components/bundle.js`, y sirve las ilustraciones que el prototipo pide como `/_blob/<id>` usando `manifest.json`. No modifica nada dentro de `design/`. No tiene dependencias: solo Node.

Pruebas: `npm test`.
