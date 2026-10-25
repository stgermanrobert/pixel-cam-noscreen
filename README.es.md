# Pixel Cam — No Screen

**Usa un teléfono Android con la pantalla rota como cámara de alta calidad en Windows: por USB y sin tocar el teléfono.**

[English](README.md) · [Guía de rescate con la pantalla rota](docs/rescue-guide.es.md)

<p align="center"><img src="docs/screenshot.png" alt="Pixel Cam" width="417"></p>

Pixel Cam es una pequeña app para Windows construida sobre [scrcpy](https://github.com/Genymobile/scrcpy). Nació para rescatar un Google Pixel 8 Pro al que se le murió la pantalla: el teléfono funciona y sus cámaras son excelentes, pero no se puede ver ni tocar nada en él. Pixel Cam permite elegir lente, zoom, rotación y calidad desde el PC, grabar vídeo y enviar la imagen a Meet, Zoom o cualquier app que acepte una webcam.

## Funciones

- **Todas las lentes que expone el teléfono**, detectadas automáticamente, incluida la gran angular (zoom por debajo de 1x).
- **Zoom, rotación, espejo, resolución (hasta 4K), formato, FPS y bitrate**: los cambios se aplican en vivo en la vista previa.
- **Grabar vídeo** directamente en MP4 o MKV, con el audio del micrófono del teléfono.
- **Enviar a Meet / Zoom / Teams** como webcam (mediante el driver OBS Virtual Camera; OBS no se abre).
- **Desbloqueo automático**: configuras el PIN una vez y la app desbloquea el teléfono antes de cada acción. El PIN se guarda cifrado para tu usuario de Windows.
- **Ver y controlar la pantalla del teléfono** desde el PC (ratón y teclado).
- **Mantiene la pantalla del teléfono encendida** mientras está enchufado, para que la cámara no se corte.
- Interfaz en inglés y español.
- No hay que instalar nada en el teléfono.

## Requisitos

| Qué | Para qué |
|---|---|
| Windows 10 u 11 | La app y la cámara virtual son solo para Windows |
| Python 3.9 o superior | Ejecuta la app ([python.org](https://www.python.org/downloads/)) |
| [scrcpy](https://github.com/Genymobile/scrcpy) | Hace la transmisión de la cámara. Probado con scrcpy 5.0.1. Incluye `adb` |
| Android 12 o superior | scrcpy lo necesita para usar la cámara del teléfono |
| **Depuración USB activada y este PC autorizado** | Si la pantalla ya está rota y no es tu caso, mira la [guía de rescate](docs/rescue-guide.es.md) |
| OBS Studio *(opcional)* | Solo para "Enviar a Meet / Zoom": al instalarlo se añade el driver de cámara virtual |

## Instalación

1. **Instala scrcpy** (incluye `adb`):
   ```powershell
   winget install Genymobile.scrcpy
   ```
2. **Descarga este proyecto**: *Code → Download ZIP* y descomprímelo, o
   ```powershell
   git clone https://github.com/stgermanrobert/pixel-cam-noscreen.git
   ```
3. *(Opcional, para Meet / Zoom)* instala OBS Studio una vez y las librerías extra de Python:
   ```powershell
   winget install OBSProject.OBSStudio
   python -m pip install -r requirements.txt
   ```
4. **Haz doble clic en `pixel_cam.pyw`.**

## Primer uso

1. Conecta el teléfono al PC con un cable USB. Arriba en la ventana debería decir *"● Pixel 8 Pro conectado por USB"* (o tu modelo).
2. Abre **⚙ Ajustes**, escribe tu **PIN** y guarda. A partir de ahí la app desbloquea el teléfono sola. *Probar desbloqueo* lo comprueba al momento.
3. La app detecta las cámaras del teléfono por su cuenta. Elige una lente, pulsa **▶ Vista previa** y ajusta.

## Uso

| Botón | Qué hace |
|---|---|
| **▶ Vista previa** | Abre una ventana con la cámara. Al cambiar cualquier ajuste se reabre sola con los nuevos valores (corte de 1–2 s). |
| **● Grabar** | Graba en tu carpeta *Vídeos\Pixel Cam* (configurable). También funciona desde la vista previa. |
| **■ Detener** | Cierra la cámara y, si estaba grabando, guarda el archivo. |
| **Ver pantalla del teléfono** | Muestra la pantalla del teléfono para usarlo con ratón y teclado. |
| **Desbloquear** | Desbloquea el teléfono con el PIN guardado. |

### Usarlo en Meet, Zoom o Teams

1. Marca **Enviar a Meet / Zoom**. Si la vista previa no estaba abierta, se abre.
2. En la llamada, elige **OBS Virtual Camera** como cámara (recarga la página si no aparece).

Consejos:
- **No minimices** la ventana de la cámara: la imagen se congelaría. Taparla con otras ventanas no es problema.
- La calidad que recibe la llamada depende del tamaño de esa ventana: hazla de al menos ~1280 px de ancho. La cámara virtual envía 1280×720.
- Si OBS está abierto con *Start Virtual Camera* activo, detenla: el driver solo admite una fuente.

## Cómo funciona

```
Cámara del teléfono ──USB──▶ scrcpy (ventana de cámara) ──▶ Pixel Cam
                                                            ├─ grabación: scrcpy escribe MP4/MKV
                                                            └─ "Enviar a Meet": captura la ventana ──▶ driver OBS Virtual Camera ──▶ Meet / Zoom
```

- scrcpy no puede cambiar los ajustes de cámara mientras funciona, así que Pixel Cam lo reinicia tras cada cambio y deja la ventana en el mismo sitio.
- La detección de pantalla bloqueada usa una heurística (`dumpsys window` muestra el foco en *NotificationShade* mientras está la pantalla de bloqueo). Probado en Android 16; otras versiones pueden comportarse distinto.

## Ajustes y privacidad

- Los ajustes se guardan en `%APPDATA%\pixel-cam-noscreen\config.json`, **nunca dentro de la carpeta del proyecto**, así que nada personal acaba en un repositorio.
- El PIN se cifra con DPAPI de Windows: solo tu usuario de Windows, en tu PC, puede descifrarlo.
- El desbloqueo funciona con **PIN o contraseña**. El patrón no está soportado.

## Solución de problemas

| Problema | Solución |
|---|---|
| "Ningún teléfono conectado" | Ejecuta `adb devices`. Si dice `unauthorized`, este PC no está autorizado: mira la [guía de rescate](docs/rescue-guide.es.md). |
| "No encuentro scrcpy" / "No encuentro adb" | Instala scrcpy con winget o indica las rutas en **⚙ Ajustes**. Si acabas de instalarlo, cierra sesión en Windows y vuelve a entrar para que aparezca en el PATH. |
| "Falta una librería" al activar Meet | El aviso copia un comando de instalación para el Python exacto que ejecuta la app. Si ese Python no tiene pip: primero `python.exe -m ensurepip --upgrade`. |
| La ventana de la cámara se cierra sola | La caja de log muestra el código de salida de scrcpy y sus últimas líneas. |
| Sigue bloqueado después de desbloquear | Revisa el PIN en Ajustes y usa *Probar desbloqueo*. |
| Se ven líneas o una barra de título en Meet | Abre un issue con una captura (el recorte de la ventana depende del escalado de Windows). |

## Limitaciones

- Solo Windows.
- El teléfono tiene que haber tenido la **depuración USB** activada antes de que se rompiera la pantalla (o tienes que poder activarla: mira la guía de rescate).
- Los ajustes de cámara no se pueden cambiar en mitad de una grabación; se aplican en la siguiente.
- En las grabaciones, la rotación se guarda como metadato del vídeo (YouTube y los reproductores normales la respetan) y **el espejo no se aplica**.

## Créditos

- [scrcpy](https://github.com/Genymobile/scrcpy) de Genymobile (Apache 2.0): hace todo el trabajo pesado.
- [pyvirtualcam](https://github.com/letmaik/pyvirtualcam), [windows-capture](https://github.com/NiiightmareXD/windows-capture), [OpenCV](https://opencv.org/), [NumPy](https://numpy.org/).
- El driver OBS Virtual Camera de [OBS Studio](https://obsproject.com/).

## Licencia

[MIT](LICENSE) © 2026 Germán Robert
