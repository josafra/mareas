# Mareas de Chipiona

Página con reloj de marea, curva del día y vista de la playa de Las Tres Piedras,
alimentada con datos reales de tablademareas.com.

## Cómo publicarla

1. Sube TODO el contenido de esta carpeta (manteniendo la estructura, incluida
   la carpeta oculta `.github/`) a la raíz de tu repositorio de GitHub.
2. Ve a **Settings → Pages** y activa "Deploy from a branch" con la rama
   `main` y la carpeta `/ (root)`.
3. Ve a la pestaña **Actions** del repo y activa los workflows si te lo pide
   (solo la primera vez).

Con eso ya está: la página se publica en
`https://TU-USUARIO.github.io/TU-REPO/`.

## Cómo se mantiene actualizada

- `data/mareas.json` empieza con los datos de junio de 2026 (los que ya
  teníamos).
- El workflow `.github/workflows/update-mareas.yml` ejecuta `scraper.py` una
  vez al mes (día 1) y va añadiendo el mes que la web tenga publicado en ese
  momento — nunca se sobrescribe un mes con menos días de los que ya tenía,
  y el año/mes se lee directamente de la página, nunca se asume.
- También puedes lanzarlo a mano: pestaña **Actions** → "Actualizar mareas de
  Chipiona" → **Run workflow**.
- Si `data/mareas.json` no tiene datos para el mes actual, la página muestra
  automáticamente los datos de referencia de junio de 2026 con un aviso, en
  vez de romperse.
