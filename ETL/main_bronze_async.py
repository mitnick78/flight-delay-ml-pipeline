import os
import sys
import time
import asyncio
import httpx
import pandas as pd # type: ignore
import psycopg2.extras # type: ignore
from tqdm import tqdm # type: ignore
from dotenv import load_dotenv # type: ignore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection
# On importe plus get_geoloc_from_code depuis api_geoloc car on crée une version asynchrone ici
from utils.fct_format_time import Fct_Arr_Es_Time_Cor, date_time_format

# ==============================================================================
#                 PARTIE ASYNCHRONE : GÉOLOCALISATION DES VILLES
# ==============================================================================

async def get_geoloc_async(client: httpx.AsyncClient, city_id: str):
    """
    Fonction asynchrone qui effectue l'appel API vers Open-Meteo pour récupérer
    la latitude et longitude d'une ville (city_id).
    L'utilisation de 'await' permet au programme de faire autre chose sans bloquer
    l'exécution, de la même manière que plusieurs serveurs servent des clients
    simultanément en restauration.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': city_id,
        'language': 'fr',
        'format': 'json',
        'count': 1
    }
    try:
        # On attend la réponse de manière asynchrone
        response = await client.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if not results:
            return None, None, city_id
            
        return results[0]["latitude"], results[0]["longitude"], city_id

    except httpx.RequestError as exc:
        print(f"Erreur requête pour {city_id}: {exc}")
        return None, None, city_id


async def update_coordinate_city_async(cur, conn):
    """
    Au lieu de demander la géolocalisation pour chaque ville les unes à la 
    suite des autres, on lance toutes les requêtes en même temps (concurrent),
    ce qui accélère prodigieusement le temps d'exécution.
    """
    # 1. On récupère les villes existantes dans la DB
    cur.execute("SELECT Id_City, Name_City FROM City")
    cities = cur.fetchall()

    coords_batch = []
    
    print("Démarrage de la récupération asynchrone des coordonnées API...")
    
    # 2. On ouvre la connexion aux API
    async with httpx.AsyncClient() as client:
        # On prépare la pile de tâches à exécuter
        tasks = [get_geoloc_async(client, city_id) for city_id, _ in cities]
        
        # 3. On traite les requêtes au fur et à mesure qu'elles se terminent
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Villes géolocalisées"):
            lat, lon, city_id = await task
            if lat is not None and lon is not None:
                coords_batch.append((lat, lon, city_id))
            else:
                coords_batch.append((None, None, city_id))

    # 4. On enregistre en masse dans la DB (de manière classique)
    print("\nMise à jour en base des coordonnées...")
    cur.executemany("""
        UPDATE City SET Latitude_City = %s, Longitude_City = %s
        WHERE Id_City = %s
    """, coords_batch)
    conn.commit()


# ==============================================================================
#                 PARTIE CLASSIQUE : DB ET MANIPULATION DES DONNÉES
# ==============================================================================

def create_materialized_view(conn):
    try:
        cur = conn.cursor()

        # Supprime si elle existe déjà
        cur.execute("DROP MATERIALIZED VIEW IF EXISTS view_flight_dates;")

        # Création de la vue
        cur.execute("""
            CREATE MATERIALIZED VIEW view_flight_dates AS 
            WITH all_cities AS (
                SELECT Id_Origin_City AS Id_City, Date_Flight FROM Flights
                UNION ALL
                SELECT Id_Dest_City AS Id_City, Date_Flight FROM Flights
            )
            SELECT 
                Id_City, 
                MIN(Date_Flight) AS min_date, 
                MAX(Date_Flight) AS max_date
            FROM all_cities
            GROUP BY Id_City;
        """)

        conn.commit()  # ✅ commit obligatoire ici car c'est une écriture

    except Exception as e:
        conn.rollback()  # annule si erreur
        print(f"Erreur lors de la création de la vue : {e}")


def main():
    start = time.time() # Début du chrono

    inserted_states = set() # Sets pour stocker les villes et états deja saisie
    inserted_cities = set()

    load_dotenv() 

    conn = None 
    try:
        conn = get_connection()
        print("Connexion à Postgres réussi !")
        

        cur = conn.cursor() # Création des tables
        cur.execute(""" 
            DROP TABLE IF EXISTS Flights CASCADE;
            DROP TABLE IF EXISTS Weather CASCADE;
            DROP TABLE IF EXISTS WeatherDesc CASCADE;      
            DROP TABLE IF EXISTS Cancel CASCADE;
            DROP TABLE IF EXISTS City CASCADE;
            DROP TABLE IF EXISTS State CASCADE;


            CREATE TABLE State (
                Id_State varchar(5) PRIMARY KEY,
                Name_State varchar(50) NOT NULL
            );


            CREATE TABLE City (
                Id_City varchar(5) PRIMARY KEY,
                Name_City varchar(100) NOT NULL,
                Latitude_City DECIMAL(9,6),
                Longitude_City DECIMAL(9,6), 
                Id_State varchar(5) NOT NULL,
                FOREIGN KEY (Id_State) REFERENCES State(Id_State)
            );


            CREATE TABLE Cancel (
                Id_Cancel varchar(1) PRIMARY KEY,
                Name_Cancel varchar(250)
            );
                    
            
            CREATE TABLE WeatherDesc (
                Weather_Code int PRIMARY KEY,
                Weather_Description varchar(100)
            );

                   
            CREATE TABLE Weather (
                Id_Weather int PRIMARY KEY,
                Temperature decimal(6,2),
                Relative_Humidity int,
                Dewpoint decimal(6,2),
                Apparent_Temperature decimal(6,2),
                Precipitation decimal(6,2),
                Rain decimal(6,2),
                Snowfall decimal(6,2),
                Snow_deph decimal(6,2),
                Vapour_Press_Deficit decimal(6,2),
                Wind_Speed_10 decimal(6,2),
                Wind_Speed_100 decimal(6,2),
                Wind_Gusts_10 decimal(6,2),
                Weather_code int,
                FOREIGN KEY (Weather_Code) REFERENCES WeatherDesc(Weather_Code)
            );

                          
            CREATE TABLE Flights (
                Id_Flight serial PRIMARY KEY,
                Flight_Number int NOT NULL,
                Date_Flight date NOT NULL,
                Day_of_Week int NOT NULL,
                Day_Flight int NOT NULL,
                Month_Flight int NOT NULL,
                Year_Flight int NOT NULL,
                Dep_CRS_Time int NOT NULL,
                Dep_CRS_Time_Cor varchar(16),
                Dep_Time int NOT NULL,   
                Dep_Delay int NOT NULL,
                Arr_CRS_Time int NOT NULL,
                Arr_Time int NOT NULL,
                Arr_Es_Time_Cor varchar(16),        
                Arr_Delay int NOT NULL,
                Estimated_Duration int NOT NULL,
                Final_Duration int NOT NULL,
                Carrier_Delay int NOT NULL,
                Weather_Delay int NOT NULL,
                NAS_Delay int NOT NULL,
                Security_Delay int NOT NULL,
                LateAircraft_Delay int NOT NULL,
                Id_Origin_City varchar(5) NOT NULL,
                Id_Dest_City varchar(5) NOT NULL,
                Id_Origin_Weather int,
                Id_Dest_Weather int,
                Id_Cancel varchar(1) NOT NULL,
                FOREIGN KEY (Id_Origin_City) REFERENCES City(Id_City),
                FOREIGN KEY (Id_Dest_City) REFERENCES City(Id_City),
                FOREIGN KEY (Id_Origin_Weather) REFERENCES Weather(Id_Weather),
                FOREIGN KEY (Id_Dest_Weather) REFERENCES Weather(Id_Weather),
                FOREIGN KEY (Id_Cancel) REFERENCES Cancel(Id_Cancel)
            );

                   
            INSERT INTO Cancel (Id_Cancel, Name_Cancel) VALUES
                ('0', 'Le vol n''a pas été annulé.'),
                ('A', 'Conditions météorologiques imprévues (ex. : tempête violente).'),
                ('B', 'Problèmes de sécurité imprévus (ex. : menace sécuritaire).'),
                ('C', 'Grèves du personnel de l''aéroport ou d''un prestataire tiers (hors grève interne à la compagnie).');
            

            INSERT INTO WeatherDesc (
                Weather_Code, 
                Weather_Description)
                VALUES
                ('0', 'Ciel clair'),
                ('1', 'Ciel généralement clair'),
                ('2', 'Ciel partiellement nuageux'),
                ('3', 'Ciel couvert'),
                ('45', 'Brouillard'),
                ('48', 'Brouillard givrant'),
                ('51', 'Bruine : Légère'),
                ('53', 'Bruine : Modérée'),
                ('55', 'Bruine : Intensité intense'),
                ('56', 'Bruine verglaçante : légère'),
                ('57', 'Bruine verglaçante : Intensité intense'),
                ('61', 'Pluie : légère'),
                ('63', 'Pluie : modérée'),
                ('65', 'Pluie : Forte intensité'),
                ('66', 'Pluie verglaçante : légère'),
                ('67', 'Pluie verglaçante : forte intensité'),
                ('71', 'Chutes de neige : légères'),
                ('73', 'Chutes de neige : modérées'),
                ('75', 'Chutes de neige : fortes intensités'),
                ('77', 'Cristaux de neige'),
                ('80', 'Averses : légères'),
                ('81', 'Averses : modérées'),
                ('82', 'Averses : Violentes'),
                ('85', 'Averses de neige : légères'),
                ('86', 'Averses de neige : fortes'),
                ('95', 'Orages : faibles ou modérés'),
                ('96', 'Orage avec un peu de grêle'),
                ('99', 'Orage avec forte grêle');


            --Création d'index pour déterminer le min/max des dates par aéroport
            CREATE INDEX idx_flights_dep_date           
            ON Flights (Id_Origin_City, Date_Flight);

            CREATE INDEX idx_flights_arr_date
            ON Flights (Id_Dest_City, Date_Flight);
        """)   
        conn.commit()
        
        print("Lecture du fichier CSV...")
        df = pd.read_csv(os.getenv("DATASET_AIRLINES"), sep=',', header=0, engine='pyarrow') # pyright: ignore[reportArgumentType] 
        
        df['CancellationCode'] = df['CancellationCode'].fillna('0') 

        cols_int = ['DepDelayMinutes', 'ArrDelayMinutes', 'CRSElapsedTime', 'ActualElapsedTime', 'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay', 'DepTime', 'ArrTime', 'DepDelay', 'ArrDelay']
        df[cols_int] = df[cols_int].fillna(0).astype(int) 

        print("Préparation en mémoire des données des vols... (extrêmement rapide)")
        state_records = {} 
        city_records = {} 
        flights_records = []

        for row in tqdm(df.itertuples(index=False), total=len(df), desc="Préparation Lignes CSV"):
            if row.OriginState not in state_records:
                state_records[row.OriginState] = (row.OriginState, row.OriginStateName)
            if row.DestState not in state_records:
                state_records[row.DestState] = (row.DestState, row.DestStateName)

            if row.Origin not in city_records:
                city_records[row.Origin] = (row.Origin, row.OriginCityName, row.OriginState)
            if row.Dest not in city_records:
                city_records[row.Dest] = (row.Dest, row.DestCityName, row.DestState)
            
            # Remplissage des champs calculés
            Arr_Es_Time_Cor = Fct_Arr_Es_Time_Cor(row.DepTime, row.CRSElapsedTime)
            Dep_CRS_Time_Cor, Arr_Es_Time_Cor = date_time_format(row.FlightDate, row.CRSDepTime, Arr_Es_Time_Cor)

            flights_records.append((
                row.Flight_Number_Operating_Airline,
                row.FlightDate,
                row.DayOfWeek,
                row.DayofMonth,
                row.Month,
                row.Year,
                row.CRSDepTime,
                Dep_CRS_Time_Cor,
                row.DepTime,
                row.DepDelay,
                row.CRSArrTime,
                row.ArrTime,
                Arr_Es_Time_Cor,
                row.ArrDelay,
                row.CRSElapsedTime,
                row.ActualElapsedTime,
                row.CarrierDelay,
                row.WeatherDelay,
                row.NASDelay,
                row.SecurityDelay,
                row.LateAircraftDelay,
                row.Origin,
                row.Dest,
                row.CancellationCode
            ))

        async def async_main_orchestrator():
            def _insert_db():
                psycopg2.extras.execute_values(cur, "INSERT INTO State (Id_State, Name_State) VALUES %s ON CONFLICT (Id_State) DO NOTHING", list(state_records.values()))
                psycopg2.extras.execute_values(cur, "INSERT INTO City (Id_City, Name_City, Id_State) VALUES %s ON CONFLICT (Id_City) DO NOTHING", list(city_records.values()))
                
                insert_flights_query = """
                    INSERT INTO Flights (
                    Flight_Number, Date_Flight, Day_of_Week, Day_Flight, Month_Flight, Year_Flight,
                    Dep_CRS_Time, Dep_CRS_Time_Cor, Dep_Time, Dep_Delay,
                    Arr_CRS_Time, Arr_Time, Arr_Es_Time_Cor, Arr_Delay,
                    Estimated_Duration, Final_Duration, Carrier_Delay, Weather_Delay,
                    NAS_Delay, Security_Delay, LateAircraft_Delay,
                    Id_Origin_City, Id_Dest_City, Id_Cancel)
                    VALUES %s
                """
                psycopg2.extras.execute_values(cur, insert_flights_query, flights_records, page_size=10000)
                conn.commit()

            print("Insertion en masse et asynchrone dans la DB... (quelques secondes)")
            await asyncio.to_thread(_insert_db)
            
            # Appel asynchrone pour la géolocalisation
            await update_coordinate_city_async(cur, conn)

        # ==================== LANCEMENT ORCHESTRATEUR ASYNCHRONE ====================
        asyncio.run(async_main_orchestrator())
        # ============================================================================

        print("\nCréation des vues matérialisées...")
        create_materialized_view(conn)
        conn.close()

        end = time.time() # Fin du chrono
        elapsed = end - start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print("\n=== Script asynchrone exécuté avec succès ! ===")
        print(f"Nombre de lignes traitées : {len(df)}")
        print(f"Temps total d'exécution : {minutes} minutes et {seconds} secondes")


    except Exception as e:
        if conn is not None:    # vérifie avant rollback
            conn.rollback()
        print(f"Erreur globale : {e}")
        raise
    finally:
        if conn is not None:    # vérifie avant close
            conn.close()

if __name__ == "__main__":
    main()
