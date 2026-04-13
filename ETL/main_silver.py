import pandas as pd
import psycopg2
import psycopg2.extras
import json
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from tqdm import tqdm
from utils.api_weather import build_weather_cache
from db.fct_silver import list_date_cities, cities_min_max
from db.connection import get_connection





def run_silver_layer():
    """
    Fonction principale qui établit la connexion à la base de données
    et exécute les traitements de la couche Silver
    """

    conn = None # Initialisation de la connexion
    weather_by_city = pd.DataFrame()
    cache_weather = pd.DataFrame()
    weather_rows = []

    try:
        # load_dotenv() # Chargement du fichier .env qui contient les informations de connexion à Postgres

        conn = get_connection()
        print("La connexion à Postgres est établie.")

        cur = conn.cursor() # Création du curseur

        cities = cities_min_max(cur) # Récupération des dates min et max de la table Flights
        colum, flights = list_date_cities(cur) # Récupération de tous les vols avec date_cor et code aéroport
        df_flights = pd.DataFrame(flights, columns=colum).set_index("id_flight")

        cache_weather = build_weather_cache(cities) # Charge toutes les données météo (1 fois)
        for airport in cache_weather:
            cache_weather[airport] = cache_weather[airport].set_index("time")
        




        for id_flight, row in tqdm(df_flights.iterrows(), total=len(df_flights)):
            dep_time = row["dep_crs_time_cor"]
            arr_time = row["arr_es_time_cor"]
            origin = row["origin"]
            dest = row["dest"]

            weather_origin = cache_weather[origin].loc[dep_time]
            weather_dest = cache_weather[dest].loc[arr_time]

            weather_rows.append({"id_weather": id_flight * 2 - 1, **weather_origin})
            weather_rows.append({"id_weather": id_flight * 2,     **weather_dest})

        weather_by_city = pd.DataFrame(weather_rows)

        
        # cur.execute("""
        #     UPDATE Flights
        #     SET id_origin_weather = NULL,
        #         id_dest_weather = NULL;
        # """)
        # conn.commit()
        
        # cur.execute("TRUNCATE TABLE Weather;")
        # conn.commit()

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


    except psycopg2.Error as error: 
       print("Erreur de connexion à Postgres : ", error)

 
    finally: 
        if conn is not None: # Fermeture de la connexion à Postgres
            conn.close()
            print("La connexion a Postgres est maintenant fermée.")


if __name__ == "__main__":
    run_silver_layer()
