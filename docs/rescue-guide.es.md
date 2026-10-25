# Rescatar un teléfono Android con la pantalla muerta

[English](rescue-guide.md) · [Volver al README](../README.es.md)

La pantalla de tu teléfono está negra (o el táctil ya no responde), pero el teléfono sigue encendido. Esta guía te da **control total desde un PC con Windows**: ver su pantalla, usarlo con ratón y teclado, hacer backup y usarlo como cámara con Pixel Cam.

Está escrita a partir de un caso real: un **Google Pixel 8 Pro con Android 16** al que primero le falló el táctil y después se le apagó la imagen. Los pasos marcados como *(sin probar)* son razonables, pero no hicieron falta en ese caso.

> **¿Por qué es difícil?** Android solo deja que un PC controle el teléfono (ADB) si la **depuración USB** está activada **y** pulsaste *"Permitir"* en el teléfono para ese PC. Esa confirmación es una medida de seguridad: sin ella, cualquiera con un cable podría entrar en un teléfono robado. No hay forma de saltársela, pero hay otras maneras de "ver" y "tocar" el teléfono.

---

## 1. ¿El teléfono está vivo?

- **Llámalo** desde otro teléfono: ¿suena o vibra?
- **Reinicio forzado:** mantén el **botón de encendido unos 30 segundos** hasta que vibre.
- **Pregúntale a ADB.** Instala Android platform-tools (o scrcpy, que incluye `adb`):
  ```powershell
  winget install Genymobile.scrcpy
  ```
  Cierra y abre PowerShell, conecta el teléfono por USB y ejecuta:
  ```powershell
  adb devices
  ```

| Resultado | Significa | Sigue en |
|---|---|---|
| `XXXXXXXX  device` | Encendido, depuración USB activada y este PC autorizado. Ya está. | [Paso 4](#4-dejarlo-permanente) |
| `XXXXXXXX  unauthorized` | Encendido y **con la depuración USB activada**, pero este PC nunca fue autorizado. | [Paso 2](#2-unauthorized-acceso-con-talkback--teclado--depuración-inalámbrica) |
| Lista vacía | Apagado, o la depuración USB está desactivada. | Mira el Administrador de dispositivos al conectarlo; prueba el [Paso 3](#3-otras-vías) |

> Si la batería se descargó del todo (por ejemplo, meses en un cajón), cárgalo un rato primero. Si la tapa trasera está **abombada** o la pantalla se despega, desenchúfalo: una batería hinchada es peligrosa.

---

## 2. `unauthorized`: acceso con TalkBack + teclado + depuración inalámbrica

La idea: **TalkBack** (el lector de pantalla de Android) lee la pantalla en voz alta, un **teclado USB** te permite moverte, y la **depuración inalámbrica** permite emparejar el PC por Wi-Fi con un código que TalkBack te dicta. No hace falta el táctil.

Necesitas: un teclado USB + un adaptador OTG USB-C (o un teclado USB-C), y el teléfono en una red Wi-Fi a la que también esté conectado el PC.

### 2.1 Activa TalkBack (tus "ojos")

**Sin nada conectado**, prueba en este orden:
1. Di **"Hey Google, activa TalkBack"**.
2. O mantén pulsados **los dos botones de volumen 3 segundos** (solo funciona si el atajo de accesibilidad estaba configurado; puede pedir repetirlo para confirmar).

Funcionó si el teléfono empieza a **hablar**. TalkBack habla en el idioma del teléfono.

### 2.2 Desbloquea con el teclado

1. Conecta el teclado al teléfono.
2. Pulsa **una vez** el botón de encendido y espera a que TalkBack diga algo (la hora, la pantalla de bloqueo…). Si dice *"screen off"* / *"pantalla apagada"*, púlsalo otra vez.
3. **Escribe tu PIN** en el teclado y pulsa **Enter**.
4. Pulsa **Tab** varias veces: si TalkBack menciona apps o la pantalla de inicio, está desbloqueado (puede decir *"device unlocked"*).

Navegación con teclado: **Tab / Shift+Tab** pasan de un elemento a otro y **Enter** activa. Si Tab no avanza, prueba **Alt + flechas** y **Alt+Enter** (atajos propios de TalkBack).

### 2.3 Activa la depuración inalámbrica

1. Di **"Hey Google, desactiva el modo avión"** y **"Hey Google, activa el Wi-Fi"** si hace falta.
2. Di **"Hey Google, abre las opciones de desarrollador"** (o ve con el teclado a Ajustes → Sistema → Opciones de desarrollador).
3. Avanza con Tab hasta **Depuración inalámbrica** (*Wireless debugging*) y actívala; acepta *"Permitir en esta red"*. TalkBack debería leer el interruptor como **activado / ON**.
4. Entra en **Depuración inalámbrica** → **Vincular dispositivo con código de vinculación**. TalkBack lee un **código de 6 dígitos** (a menudo como número: *"ciento veintitrés mil…"*) y una IP:puerto. **Deja ese diálogo abierto.**

### 2.4 Empareja desde el PC

No hace falta que entiendas la IP ni el puerto de oído: el PC los encuentra solo.

```powershell
adb mdns services
```

Verás líneas así:

```
adb-XXXXXXXX-xxxx   _adb-tls-pairing._tcp   192.168.1.50:41393
adb-XXXXXXXX-xxxx   _adb-tls-connect._tcp   192.168.1.50:45435
```

- `_adb-tls-pairing` → puerto para **emparejar** (solo aparece mientras el diálogo de vinculación está abierto).
- `_adb-tls-connect` → puerto para **conectar**.

```powershell
adb pair 192.168.1.50:41393 123456      # puerto de pairing + el código de 6 dígitos
adb connect 192.168.1.50:45435          # puerto de conexión
adb devices
```

Lecciones del caso real:
- Usar el puerto de **conexión** con `adb pair` falla con `protocol fault`. Hay que usar el de **pairing**.
- El **código cambia** cada vez que reabres el diálogo. Si falla, vuelve a abrirlo, escucha de nuevo (Shift+Tab y luego Tab repiten el elemento) y repite `adb mdns services`.

### 2.5 Ve la pantalla

```powershell
scrcpy
```

Ya ves el teléfono en el PC y lo controlas con ratón y teclado. Lo primero: **desactiva TalkBack** (*"Hey Google, desactiva TalkBack"*), porque con TalkBack activo los clics se comportan distinto.

---

## 3. Otras vías

**Salida de vídeo por USB-C**: los Pixel 8, 8 Pro y 8a pueden sacar vídeo por USB-C (DisplayPort Alt Mode) desde el feature drop de junio de 2024. Con un **hub USB-C con HDMI + puertos USB + carga PD** puedes conectar a la vez una TV o monitor, un ratón y un teclado, y usar el teléfono normalmente. A tener en cuenta:
- Tiene que ser un adaptador **DP Alt Mode** de verdad. Los adaptadores tipo "tarjeta gráfica USB" que necesitan driver (estilo DisplayLink, por ejemplo USB-A a HDMI) **no sirven**.
- Al conectar una pantalla, el teléfono puede preguntar en su propia pantalla si quieres duplicarla; quizá haya que aceptarlo a ciegas con el teclado *(sin probar)*.

**Un PC que ya estaba autorizado**: la autorización está ligada a los archivos `%USERPROFILE%\.android\adbkey` y `adbkey.pub` del PC. Si alguna vez autorizaste otro ordenador ("Permitir siempre"), copia esos dos archivos a la misma carpeta de este PC y ejecuta `adb kill-server` y `adb devices`.

**La depuración USB nunca estuvo activada** *(sin probar)*: con TalkBack + teclado, en teoría podrías ir a Ajustes → Información del teléfono, pulsar Enter **7 veces** sobre *Número de compilación* para activar las Opciones de desarrollador, y seguir con el [paso 2.3](#23-activa-la-depuración-inalámbrica). Si tampoco se puede activar TalkBack, la opción realista es **cambiar la pantalla**.

**Lo que no va a funcionar**: saltarse el diálogo de autorización de ADB (está diseñado para impedirlo) y desbloquear el bootloader (requiere *Desbloqueo OEM* activado de antemano y **borra todos los datos**).

---

## 4. Dejarlo permanente

Hazlo ahora, mientras tienes el control:

1. **Autoriza el USB para siempre:** conecta el teléfono al PC por USB. En la ventana de scrcpy aparece *"¿Permitir depuración USB?"*: marca **"Permitir siempre desde este ordenador"** y pulsa **Permitir**. La depuración inalámbrica se apaga en cada reinicio; la autorización USB queda.
2. **Activa "Desactivar tiempo de espera de autorización de adb"** en Opciones de desarrollador, para que la autorización no caduque tras 7 días sin conectar.
3. **Haz backup de las claves del PC** (`%USERPROFILE%\.android\adbkey` y `adbkey.pub`) en un sitio seguro y privado. Si reinstalas Windows, vuelves a copiarlas y el teléfono te sigue reconociendo. `adbkey` es una clave privada: no la compartas.
4. **Haz backup del teléfono** (fotos, apps de 2FA) mientras puedes verlo.

A partir de ahí, con el cable conectado, `scrcpy` (o Pixel Cam) funciona directo: sin Wi-Fi ni TalkBack.

---

## 5. Úsalo como cámara

Abre [Pixel Cam](../README.es.md), configura tu PIN en Ajustes y listo.

Como alternativa, Android 14+ tiene un modo USB **Webcam** nativo (notificación de USB → *Webcam*) que Windows ve como una cámara normal sin software extra. Es más simple, pero pierdes los controles de lente, zoom y rotación de Pixel Cam.
