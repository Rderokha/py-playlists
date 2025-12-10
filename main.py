import time
import os
import spotipy
import tidalapi
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

def connect_spotify():
    """Inicializa la sesión de Spotify usando variables de entorno."""
    try:
        # Scope necesario para leer tus listas privadas
        scope = "playlist-read-private user-library-read"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        user = sp.me()
        print(f"✅ [Spotify] Conectado como: {user['display_name']}")
        return sp
    except Exception as e:
        print(f"❌ [Spotify] Error de conexión: {e}")
        exit()

def connect_tidal():
    """Inicializa la sesión de Tidal."""
    print("🔄 [Tidal] Iniciando autenticación (sigue las instrucciones si aparecen)...")
    session = tidalapi.Session()
    try:
        # login_oauth_simple imprimirá una URL en consola si no hay sesión guardada
        session.login_oauth_simple()
        if session.check_login():
            print(f"✅ [Tidal] Conectado como: {session.user.username}")
            return session
    except Exception as e:
        print(f"❌ [Tidal] Error de conexión: {e}")
        exit()

def listar_y_seleccionar_playlist(sp):
    """Obtiene las playlists del usuario + Canciones que te gustan."""
    print("\n⬇️  Obteniendo tus playlists de Spotify...")
    
    playlists = []

    # 1. Obtener 'Tus Me Gusta' (Saved Tracks)
    # Hacemos una petición rápida solo para saber el total
    saved_tracks_info = sp.current_user_saved_tracks(limit=1)
    total_likes = saved_tracks_info['total']
    
    # Creamos una 'playlist falsa' para representarla en el menú
    liked_songs_playlist = {
        'name': '❤️  Canciones que te gustan',
        'id': 'LIKED_SONGS_ID', # ID especial interno para identificarla
        'tracks': {'total': total_likes}
    }
    playlists.append(liked_songs_playlist)

    # 2. Obtener playlists normales
    results = sp.current_user_playlists(limit=50)
    playlists.extend(results['items'])
    
    if not playlists:
        print("⚠️ No se encontraron playlists.")
        exit()

    # Mostrar lista numerada
    print(f"\n{'#':<4} {'Nombre':<40} {'Tracks'}")
    print("-" * 60)
    
    for i, pl in enumerate(playlists):
        nombre = pl['name'][:37] + "..." if len(pl['name']) > 37 else pl['name']
        # Manejo seguro por si alguna playlist viene sin conteo exacto
        total_tracks = pl['tracks']['total']
        print(f"{i+1:<4} {nombre:<40} {total_tracks}")

    print("-" * 60)

    while True:
        try:
            selection = input("\n👉 Ingresa el NÚMERO de la playlist a migrar: ")
            index = int(selection) - 1
            if 0 <= index < len(playlists):
                selected_playlist = playlists[index]
                print(f"\n✅ Has seleccionado: {selected_playlist['name']}")
                return selected_playlist
            else:
                print("❌ Número fuera de rango.")
        except ValueError:
            print("❌ Por favor, ingresa un número válido.")

def obtener_tracks_spotify(sp, playlist_id):
    """Extrae canciones, manejando tanto playlists normales como 'Me gusta'."""
    tracks_data = []
    
    # Función auxiliar para procesar un lote de items
    def procesar_items(items):
        for item in items:
            if item['track']: 
                track = item['track']
                artist_name = track['artists'][0]['name']
                track_name = track['name']
                tracks_data.append({
                    'artist': artist_name,
                    'track': track_name,
                    'uri': track['uri']
                })

    if playlist_id == 'LIKED_SONGS_ID':
        print("   -> Descargando 'Me gusta' (esto puede tardar si son muchas)...")
        # Paginación para Saved Tracks
        results = sp.current_user_saved_tracks(limit=50)
        procesar_items(results['items'])
        
        while results['next']:
            results = sp.next(results)
            procesar_items(results['items'])
            
    else:
        # Paginación para Playlists Normales
        results = sp.playlist_tracks(playlist_id)
        procesar_items(results['items'])
        
        while results['next']:
            results = sp.next(results)
            procesar_items(results['items'])
            
    return tracks_data

def migrar_a_tidal(session, playlist_name, tracks_data):
    """
    Crea la playlist en Tidal y busca/agrega las canciones una por una.
    """
    print(f"\n🚀 Creando playlist en Tidal: '{playlist_name}'...")
    
    # 1. Crear la playlist vacía en Tidal
    try:
        new_playlist = session.user.create_playlist(playlist_name, "Migrada desde Spotify con Python")
        print(f"✅ Playlist creada con ID: {new_playlist.id}")
    except Exception as e:
        print(f"❌ Error creando playlist: {e}")
        return

    found_count = 0
    missing_tracks = []
    
    print("\n🔍 Iniciando búsqueda y transferencia...")
    print("-" * 60)

    # 2. Iterar sobre las canciones
    for i, item in enumerate(tracks_data):
        artist = item['artist']
        track = item['track']
        
        # Construimos la query de búsqueda: "Artista Canción"
        # Esto suele ser más preciso que buscar solo el nombre de la canción
        search_query = f"{artist} {track}"
        
        try:
            # Buscamos en Tidal (Limitamos a 1 resultado para ser eficientes)
            # models=[tidalapi.media.Track] asegura que solo busquemos canciones, no videos ni álbumes
            search_results = session.search(search_query, models=[tidalapi.media.Track], limit=1)
            
            # Verificamos si encontramos algo en la lista de 'tracks'
            if search_results['tracks']:
                tidal_track = search_results['tracks'][0]
                
                # Agregamos a la playlist
                new_playlist.add([tidal_track.id])
                
                print(f"[{i+1}/{len(tracks_data)}] ✅ {track[:30]}...")
                found_count += 1
            else:
                print(f"[{i+1}/{len(tracks_data)}] ❌ NO ENCONTRADA: {track} - {artist}")
                missing_tracks.append(f"{artist} - {track}")
                
        except Exception as e:
            print(f"[{i+1}/{len(tracks_data)}] ⚠️ Error procesando: {e}")
            missing_tracks.append(f"{artist} - {track} (Error API)")

        # 3. Pequeña pausa para evitar rate-limiting (respeto a la API)
        time.sleep(0.5) 

    # 4. Resumen final
    print("-" * 60)
    print(f"🏁 Proceso terminado.")
    print(f"Total procesado: {len(tracks_data)}")
    print(f"Exitosas: {found_count}")
    print(f"Fallidas: {len(missing_tracks)}")
    
    if missing_tracks:
        print("\n📝 Canciones que NO se pudieron migrar:")
        for missing in missing_tracks:
            print(f" - {missing}")

def main():
    print("=== MIGRATOR SPOTIFY TO TIDAL ===\n")
    
    # 1. Conexiones
    sp = connect_spotify()
    tidal = connect_tidal()

    # 2. Selección de Playlist
    playlist_sp = listar_y_seleccionar_playlist(sp)
    
    # 3. Extracción de datos
    print(f"\n📖 Leyendo canciones de '{playlist_sp['name']}'...")
    tracks = obtener_tracks_spotify(sp, playlist_sp['id'])
    print(f"Total canciones encontradas: {len(tracks)}")
    
    if not tracks:
        print("La playlist está vacía. Finalizando.")
        return

    # 4. Confirmación
    confirm = input(f"\n¿Quieres migrar {len(tracks)} canciones a Tidal ahora? (s/n): ")
    
    if confirm.lower() == 's':
        # Definir nombre para la nueva playlist
        nombre_tidal = input(f"Nombre para la playlist en Tidal [{playlist_sp['name']}]: ")
        if not nombre_tidal:
            nombre_tidal = playlist_sp['name']
            
        # Llamar a la función de migración
        migrar_a_tidal(tidal, nombre_tidal, tracks)
    else:
        print("Operación cancelada.")

if __name__ == "__main__":
    main()