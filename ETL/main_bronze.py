
from dotenv import load_dotenv # type: ignore
from tqdm import tqdm # type: ignore
import pandas as pd # type: ignore
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from db.connection import get_connection
from utils.api_geoloc import get_geoloc_from_code # type: ignore
from utils.fct_format_time import Fct_Arr_Es_Time_Cor, date_time_format


start = time.time() # Début du chrono

inserted_states = set() # Sets pour stocker les villes et états deja saisie
inserted_cities = set()


#load_dotenv() # On charge le fichier .env qui a les informations de connexion à Postgres


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


def update_coordinate_city(cur, conn):
    # 1. Récupère toutes les villes en une seule requête
    cur.execute("SELECT Id_City, Name_City FROM City")
    cities = cur.fetchall()

    #Prépare un batch de coords
    coords_batch = []
    for city_id, _ in tqdm(cities):
        try:
            
            result = get_geoloc_from_code(city_id)
            if result is not None:
                lat = result["lat"]
                lon = result["lng"]
                coords_batch.append((lat, lon, city_id))
            
        except Exception as e:
            print(f"Erreur pour {city_id}: {e}")
            coords_batch.append((None, None, city_id))  # On skippe sans bloquer

    #3. UPDATE en une seule fois avec executemany
    cur.executemany("""
        UPDATE City SET Latitude_City = %s, Longitude_City = %s
        WHERE Id_City = %s
    """, coords_batch)
    conn.commit()

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
    

    df = pd.read_csv(os.getenv("DATASET_AIRLINES"), sep=',', header=0, engine='pyarrow') # pyright: ignore[reportArgumentType] # On charge le CSV dans la variable _df_ + Mettre DATASET_AIRLINES dans le .env
    
    df['CancellationCode'] = df['CancellationCode'].fillna('0') # Remplace CancellationCode par 0 lorsque le vol n'est pas annulé

    cols_int = ['DepDelayMinutes', 'ArrDelayMinutes', 'CRSElapsedTime', 'ActualElapsedTime', 'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay', 'DepTime', 'ArrTime', 'DepDelay', 'ArrDelay']
    df[cols_int] = df[cols_int].fillna(0).astype(int) # On convertis les formats .0 en entier, en tenant compte des NaN qu'on remplace par 0


    for index, row in tqdm(df.iterrows(), total=len(df)): # On parcours toutes les lignes du CSV - TQDM = barre de chargement
        if index % 1000 == 0: # On commit toutes les 1000 lignes
            conn.commit()
        
        if row['OriginState'] not in inserted_states:
            cur.execute("""
                INSERT INTO State (
                Id_State,
                Name_State)
                    VALUES (%s, %s)
                """, (
                row['OriginState'],
                row['OriginStateName']))
            inserted_states.add(row['OriginState'])

        if row['DestState'] not in inserted_states:           
            cur.execute("""
                INSERT INTO State (
                Id_State,
                Name_State)
                    VALUES (%s, %s)
                """, (
                row['DestState'],
                row['DestStateName']))
            inserted_states.add(row['DestState'])      

        if row['Origin'] not in inserted_cities:
            cur.execute("""
                INSERT INTO City (
                Id_City,
                Name_City,
                Id_State)
                    VALUES (%s, %s, %s)
                """, (
                row['Origin'],
                row['OriginCityName'],
                row['OriginState']))
            inserted_cities.add(row['Origin'])

        if row['Dest'] not in inserted_cities:          
            cur.execute("""
                INSERT INTO City (
                Id_City,
                Name_City,
                Id_State)
                    VALUES (%s, %s, %s)
                """, (
                row['Dest'],
                row['DestCityName'],
                row['DestState']))
            inserted_cities.add(row['Dest'])
        
        # Remplissage des champs calculés
        Arr_Es_Time_Cor = Fct_Arr_Es_Time_Cor(row['DepTime'],row['CRSElapsedTime'])
        Dep_CRS_Time_Cor, Arr_Es_Time_Cor = date_time_format(row['FlightDate'], row['CRSDepTime'], Arr_Es_Time_Cor)

        cur.execute("""
            INSERT INTO Flights (
            Flight_Number,
            Date_Flight,
            Day_of_Week,
            Day_Flight,
            Month_Flight,
            Year_Flight,
            Dep_CRS_Time,
            Dep_CRS_Time_Cor,
            Dep_Time,
            Dep_Delay,
            Arr_CRS_Time,
            Arr_Time,
            Arr_Es_Time_Cor,
            Arr_Delay,
            Estimated_Duration,
            Final_Duration,
            Carrier_Delay,
            Weather_Delay,
            NAS_Delay,
            Security_Delay,
            LateAircraft_Delay,
            Id_Origin_City,
            Id_Dest_City,
            Id_Cancel)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            row['Flight_Number_Operating_Airline'],
            row['FlightDate'],
            row['DayOfWeek'],
            row['DayofMonth'],
            row['Month'],
            row['Year'],
            row['CRSDepTime'],
            Dep_CRS_Time_Cor,
            row['DepTime'],
            row['DepDelay'],
            row['CRSArrTime'],
            row['ArrTime'],
            Arr_Es_Time_Cor,
            row['ArrDelay'],
            row['CRSElapsedTime'],
            row['ActualElapsedTime'],
            row['CarrierDelay'],
            row['WeatherDelay'],
            row['NASDelay'],
            row['SecurityDelay'],
            row['LateAircraftDelay'],
            row['Origin'],
            row['Dest'],
            row['CancellationCode']))
    
    conn.commit()
    update_coordinate_city(cur, conn)
    create_materialized_view(conn)
    conn.close()

    end = time.time() # Fin du chrono
    elapsed = end - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    print("Script executé avec succés !")
    print(f"Nombre de lignes traitées : {len(df)}")
    print(f"Temps d'exécution : {minutes} minutes et {seconds} secondes")


except Exception as e:
    if conn is not None:    # ← vérifie avant rollback
        conn.rollback()
    print(f"Erreur : {e}")
    raise
finally:
    if conn is not None:    # ← vérifie avant close
        conn.close()




