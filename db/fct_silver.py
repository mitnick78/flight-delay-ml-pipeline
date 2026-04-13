def list_date_cities(cur):
    cur.execute("""          
    SELECT id_flight, dep_crs_time_cor, arr_es_time_cor, co.id_city as origin, cd.id_city as dest
    from flights f
    join city co on co.id_city = f.id_origin_city
    join city cd on cd.id_city = f.id_dest_city
    """)
    colonnes = [desc[0] for desc in cur.description]
    return colonnes, cur.fetchall()



def cities_min_max(cur):
    cur.execute("""
    SELECT c.id_city, c.latitude_city, c.Longitude_city, v.min_date, v.max_date
    FROM city c
    JOIN view_flight_dates v ON c.id_City = v.id_City
    GROUP BY c.Id_City, v.min_date, v.max_date;
    """)
    return cur.fetchall()
