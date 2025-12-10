# Spotify to Tidal Migrator

Script en Python para migrar playlists automáticamente desde Spotify hacia Tidal. Utiliza la API oficial de Spotify y `tidalapi` para interactuar con Tidal.

## 📋 Requisitos

* Python 3.8+
* Cuenta de Spotify Premium (recomendado)
* Cuenta de Tidal (HiFi/Plus)
* Credenciales de Spotify Developer

## 🚀 Instalación

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/TU_USUARIO/spotify-to-tidal-migrator.git](https://github.com/TU_USUARIO/spotify-to-tidal-migrator.git)
    cd spotify-to-tidal-migrator
    ```

2.  Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## ⚙️ Configuración

1.  Crea un archivo `.env` en la raíz del proyecto.
2.  Agrega tus credenciales (obtenidas en Spotify for Developers):

    ```env
    SPOTIPY_CLIENT_ID=tu_client_id
    SPOTIPY_CLIENT_SECRET=tu_client_secret
    SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
    ```

## ▶️ Uso

Ejecuta el script principal:

```bash
python main.py