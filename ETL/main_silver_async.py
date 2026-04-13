import pandas as pd # type: ignore
import psycopg2 # type: ignore
import psycopg2.extras # type: ignore
import os
import sys
import time
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv # type: ignore
from tqdm import tqdm # type: ignore
from db.fct_silver import list_date_cities, cities_min_max
from db.connection import get_connection
from utils.api_weather import get_weather

# ==============================================================================
#                 PARTIE ASYNCHRONE : CHARGEMENT DE LA MÉTÉO
# ==============================================================================

async def fetch_weather_task(id_city, lat, lon, min_date, max_date):
    """
    Exécute la fonction 'get_weather' originale dans un thread séparé de 
    manière asynchrone afin de la paralléliser sans la réécrire.
    """
    df = await asyncio.to_thread(get_weather, lat, lon, str(min_date), str(max_date))
    return id_city, df

async def build_weather_cache_async(cities: list) -> dict:
    """
    Crée le cache météo en récupérant les données asynchrones sans dépasser
    la limite stricte de 600 appels / minute (10 appels / seconde max).
    """
    cache = {}
    tasks = []
    
    print("Préparation de la file d'attente (respect de la limite 600/min)...")
    for city in cities:
        id_city, lat, lon, min_date, max_date = city
        task = asyncio.create_task(fetch_weather_task(id_city, lat, lon, min_date, max_date))
        tasks.append(task)
        # 0.11s d'attente = ~9 appels/sec maximum, bien en dessous de la limite
        await asyncio.sleep(0.11)
            
    print("Lancement et attente des requêtes météo...")
    for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Chargement météo asynchrone"):
        id_city, result_df = await task
        if result_df is not None:
            cache[id_city] = result_df
                
    print(f"Cache météo terminé : {len(cache)} villes chargées.")
    return cache


# ==============================================================================
#                 PARTIE CLASSIQUE : DB ET ANALYSE
# ==============================================================================

def run_silver_layer_async():
    """
    Fonction principale qui établit la connexion à la base de données
    et exécute les traitements de la couche Silver (version très accélérée)
    """

    conn = None 
    weather_by_city = pd.DataFrame()
    cache_weather = pd.DataFrame()
    weather_rows = []

    try:
        load_dotenv()

        conn = get_connection()
        print("La connexion à Postgres est établie.")

        cur = conn.cursor()

        print("Récupération des listes de villes et vols depuis Postgres...")
        cities = cities_min_max(cur) 
        colum, flights = list_date_cities(cur) 
        df_flights = pd.DataFrame(flights, columns=colum).set_index("id_flight")

        # ====================== NOUVEAU ======================
        # On lance avec asyncio.run toute la mécanique rapide
        # de téléchargement concurrent de la météo :
        cache_weather = asyncio.run(build_weather_cache_async(cities))
        # ======================================================

        # On indexe tous les dataframes reçus par la colonne 'time'
        print("Indexation...")
        for airport in cache_weather:
            cache_weather[airport] = cache_weather[airport].set_index("time")
        
        print("Mise en correspondance vols -> météo...")
        # Attention, cette boucle sur les DataFrames est purement synchrone et rapide !
        for id_flight, row in tqdm(df_flights.iterrows(), total=len(df_flights)):
            dep_time = row["dep_crs_time_cor"]
            arr_time = row["arr_es_time_cor"]
            origin = row["origin"]
            dest = row["dest"]

            try:
                weather_origin = cache_weather[origin].loc[dep_time]
                weather_dest = cache_weather[dest].loc[arr_time]

                weather_rows.append({"id_weather": id_flight * 2 - 1, **weather_origin})
                weather_rows.append({"id_weather": id_flight * 2,     **weather_dest})
            except KeyError as e:
                # Sécurité au cas où la date météo est manquante dans nos DataFrames
                pass

        weather_by_city = pd.DataFrame(weather_rows)

        print("Préparation des données pour l'insertion rapide...")
        records = [
            (
                int(w.id_weather),
                float(w.temperature_2m),
                int(w.relative_humidity_2m),
                float(w.dew_point_2m),
                float(w.apparent_temperature),
                float(w.precipitation),
                float(w.rain),
                float(w.snowfall),
                float(w.snow_depth),
                float(w.vapour_pressure_deficit),
                float(w.wind_speed_10m),
                float(w.wind_speed_100m),
                float(w.wind_gusts_10m),
                int(w.weather_code)
            )
            for w in weather_by_city.itertuples(index=False)
        ]

        insert_query = """
            INSERT INTO Weather (
                Id_Weather,
                Temperature,
                Relative_Humidity,
                Dewpoint,
                Apparent_Temperature,
                Precipitation,
                Rain,
                Snowfall,
                Snow_deph,
                Vapour_Press_Deficit,
                Wind_Speed_10,
                Wind_Speed_100,
                Wind_Gusts_10,
                Weather_code
            ) VALUES %s
            ON CONFLICT (Id_Weather) DO NOTHING
        """

        print("Insertion avec execute_values...")
        psycopg2.extras.execute_values(
            cur,
            insert_query,
            records,
            page_size=10000
        )
        conn.commit()

        print("Mise à jour des identifiants météo dans la table Flights...")
        cur.execute("""
            UPDATE Flights
            SET id_origin_weather = id_flight * 2 - 1,
                id_dest_weather = id_flight * 2;
        """)
        conn.commit()
        print("TERMINE AVEC SUCCES.")


    except psycopg2.Error as error: 
       print("Erreur de connexion à Postgres : ", error)

 
    finally: 
        if conn is not None: 
            conn.close()
            print("La connexion a Postgres est maintenant fermée.")


if __name__ == "__main__":
    start = time.time()
    run_silver_layer_async()
    end = time.time() # Fin du chrono
    elapsed = end - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    print(f"Temps total du traitement silver : {minutes} minutes et {seconds} secondes")
