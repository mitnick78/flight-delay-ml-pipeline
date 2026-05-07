import { useState } from "react";
import ViewPredict from "./components/ViewPredict";
import { getRoundedHourFormatted } from "./utils/toolsDate";
import type { PredictData } from "./types/predict.type";
import type { CityWithoutLocation } from "./types/city.types";
import type { FlightForm } from "./types/flight.type";
import ButtonCustom from "./components/Button/ButtonCustom";

const CITIES: CityWithoutLocation[] = [
  { id_city: "MHT", name_city: "Manchester, NH" },
  { id_city: "EWR", name_city: "Newark, NJ" },
  { id_city: "IAD", name_city: "Washington, DC" },
  { id_city: "STL", name_city: "St. Louis, MO" },
  { id_city: "ORD", name_city: "Chicago, IL" },
  { id_city: "ILM", name_city: "Wilmington, NC" },
  { id_city: "RIC", name_city: "Richmond, VA" },
  { id_city: "PQI", name_city: "Presque Isle/Houlton, ME" },
  { id_city: "ALB", name_city: "Albany, NY" },
  { id_city: "DCA", name_city: "Washington, DC" },
  { id_city: "LNK", name_city: "Lincoln, NE" },
  { id_city: "AVL", name_city: "Asheville, NC" },
  { id_city: "SDF", name_city: "Louisville, KY" },
  { id_city: "PWM", name_city: "Portland, ME" },
  { id_city: "PHL", name_city: "Philadelphia, PA" },
  { id_city: "SCE", name_city: "State College, PA" },
  { id_city: "DAY", name_city: "Dayton, OH" },
  { id_city: "ORF", name_city: "Norfolk, VA" },
  { id_city: "ROC", name_city: "Rochester, NY" },
  { id_city: "ITH", name_city: "Ithaca/Cortland, NY" },
  { id_city: "MDT", name_city: "Harrisburg, PA" },
  { id_city: "DTW", name_city: "Detroit, MI" },
  { id_city: "AVP", name_city: "Scranton/Wilkes-Barre, PA" },
  { id_city: "FSD", name_city: "Sioux Falls, SD" },
  { id_city: "IAH", name_city: "Houston, TX" },
  { id_city: "LCH", name_city: "Lake Charles, LA" },
  { id_city: "HSV", name_city: "Huntsville, AL" },
  { id_city: "CPR", name_city: "Casper, WY" },
  { id_city: "DEN", name_city: "Denver, CO" },
  { id_city: "HOB", name_city: "Hobbs, NM" },
  { id_city: "TYS", name_city: "Knoxville, TN" },
  { id_city: "CAE", name_city: "Columbia, SC" },
  { id_city: "TUL", name_city: "Tulsa, OK" },
  { id_city: "COD", name_city: "Cody, WY" },
  { id_city: "LBB", name_city: "Lubbock, TX" },
  { id_city: "SYR", name_city: "Syracuse, NY" },
  { id_city: "SGF", name_city: "Springfield, MO" },
  { id_city: "SHV", name_city: "Shreveport, LA" },
  { id_city: "LFT", name_city: "Lafayette, LA" },
  { id_city: "MOB", name_city: "Mobile, AL" },
  { id_city: "BRO", name_city: "Brownsville, TX" },
  { id_city: "MFE", name_city: "Mission/McAllen/Edinburg, TX" },
  { id_city: "JAN", name_city: "Jackson/Vicksburg, MS" },
  { id_city: "LIT", name_city: "Little Rock, AR" },
  { id_city: "CHO", name_city: "Charlottesville, VA" },
  { id_city: "AMA", name_city: "Amarillo, TX" },
  { id_city: "BUF", name_city: "Buffalo, NY" },
  { id_city: "PNS", name_city: "Pensacola, FL" },
  { id_city: "PVD", name_city: "Providence, RI" },
  { id_city: "ROA", name_city: "Roanoke, VA" },
  { id_city: "BHM", name_city: "Birmingham, AL" },
  { id_city: "DRO", name_city: "Durango, CO" },
  { id_city: "LRD", name_city: "Laredo, TX" },
  { id_city: "SAF", name_city: "Santa Fe, NM" },
  { id_city: "CRP", name_city: "Corpus Christi, TX" },
  { id_city: "MAF", name_city: "Midland/Odessa, TX" },
  { id_city: "ECP", name_city: "Panama City, FL" },
  { id_city: "GPT", name_city: "Gulfport/Biloxi, MS" },
  { id_city: "HRL", name_city: "Harlingen/San Benito, TX" },
  { id_city: "ICT", name_city: "Wichita, KS" },
  { id_city: "XNA", name_city: "Fayetteville, AR" },
  { id_city: "MSN", name_city: "Madison, WI" },
  { id_city: "GRB", name_city: "Green Bay, WI" },
  { id_city: "CLT", name_city: "Charlotte, NC" },
  { id_city: "LGA", name_city: "New York, NY" },
  { id_city: "ELP", name_city: "El Paso, TX" },
  { id_city: "SAV", name_city: "Savannah, GA" },
  { id_city: "DFW", name_city: "Dallas/Fort Worth, TX" },
  { id_city: "DSM", name_city: "Des Moines, IA" },
  { id_city: "OMA", name_city: "Omaha, NE" },
  { id_city: "OKC", name_city: "Oklahoma City, OK" },
  { id_city: "MCI", name_city: "Kansas City, MO" },
  { id_city: "SRQ", name_city: "Sarasota/Bradenton, FL" },
  { id_city: "MSY", name_city: "New Orleans, LA" },
  { id_city: "ATL", name_city: "Atlanta, GA" },
  { id_city: "SAT", name_city: "San Antonio, TX" },
  { id_city: "AUS", name_city: "Austin, TX" },
  { id_city: "RAP", name_city: "Rapid City, SD" },
  { id_city: "MEM", name_city: "Memphis, TN" },
  { id_city: "PHX", name_city: "Phoenix, AZ" },
  { id_city: "PIT", name_city: "Pittsburgh, PA" },
  { id_city: "TUS", name_city: "Tucson, AZ" },
  { id_city: "JAX", name_city: "Jacksonville, FL" },
  { id_city: "BZN", name_city: "Bozeman, MT" },
  { id_city: "IND", name_city: "Indianapolis, IN" },
  { id_city: "BIL", name_city: "Billings, MT" },
  { id_city: "MSP", name_city: "Minneapolis, MN" },
  { id_city: "BDL", name_city: "Hartford, CT" },
  { id_city: "GUC", name_city: "Gunnison, CO" },
  { id_city: "BNA", name_city: "Nashville, TN" },
  { id_city: "IDA", name_city: "Idaho Falls, ID" },
  { id_city: "BTR", name_city: "Baton Rouge, LA" },
  { id_city: "CLE", name_city: "Cleveland, OH" },
  { id_city: "CVG", name_city: "Cincinnati, OH" },
  { id_city: "ABQ", name_city: "Albuquerque, NM" },
  { id_city: "CMH", name_city: "Columbus, OH" },
  { id_city: "COS", name_city: "Colorado Springs, CO" },
  { id_city: "GSO", name_city: "Greensboro/High Point, NC" },
  { id_city: "RDU", name_city: "Raleigh/Durham, NC" },
  { id_city: "GRR", name_city: "Grand Rapids, MI" },
  { id_city: "CHS", name_city: "Charleston, SC" },
  { id_city: "GJT", name_city: "Grand Junction, CO" },
  { id_city: "BTV", name_city: "Burlington, VT" },
  { id_city: "MTJ", name_city: "Montrose/Delta, CO" },
  { id_city: "PIA", name_city: "Peoria, IL" },
  { id_city: "SLC", name_city: "Salt Lake City, UT" },
  { id_city: "MKE", name_city: "Milwaukee, WI" },
  { id_city: "TVC", name_city: "Traverse City, MI" },
  { id_city: "FNT", name_city: "Flint, MI" },
  { id_city: "GSP", name_city: "Greer, SC" },
  { id_city: "MLI", name_city: "Moline, IL" },
  { id_city: "CID", name_city: "Cedar Rapids/Iowa City, IA" },
  { id_city: "CAK", name_city: "Akron, OH" },
  { id_city: "SMF", name_city: "Sacramento, CA" },
  { id_city: "SNA", name_city: "Santa Ana, CA" },
  { id_city: "TPA", name_city: "Tampa, FL" },
  { id_city: "BWI", name_city: "Baltimore, MD" },
  { id_city: "DAL", name_city: "Dallas, TX" },
  { id_city: "FLL", name_city: "Fort Lauderdale, FL" },
  { id_city: "HOU", name_city: "Houston, TX" },
  { id_city: "LAS", name_city: "Las Vegas, NV" },
  { id_city: "MCO", name_city: "Orlando, FL" },
  { id_city: "MDW", name_city: "Chicago, IL" },
  { id_city: "RSW", name_city: "Fort Myers, FL" },
  { id_city: "PSP", name_city: "Palm Springs, CA" },
  { id_city: "OAK", name_city: "Oakland, CA" },
  { id_city: "SJC", name_city: "San Jose, CA" },
  { id_city: "RNO", name_city: "Reno, NV" },
  { id_city: "BUR", name_city: "Burbank, CA" },
  { id_city: "LAX", name_city: "Los Angeles, CA" },
  { id_city: "LGB", name_city: "Long Beach, CA" },
  { id_city: "SAN", name_city: "San Diego, CA" },
  { id_city: "BOI", name_city: "Boise, ID" },
  { id_city: "HNL", name_city: "Honolulu, HI" },
  { id_city: "SFO", name_city: "San Francisco, CA" },
  { id_city: "SBA", name_city: "Santa Barbara, CA" },
  { id_city: "SEA", name_city: "Seattle, WA" },
  { id_city: "EUG", name_city: "Eugene, OR" },
  { id_city: "GEG", name_city: "Spokane, WA" },
  { id_city: "KOA", name_city: "Kona, HI" },
  { id_city: "LIH", name_city: "Lihue, HI" },
  { id_city: "OGG", name_city: "Kahului, HI" },
  { id_city: "ONT", name_city: "Ontario, CA" },
  { id_city: "PDX", name_city: "Portland, OR" },
  { id_city: "SJU", name_city: "San Juan, PR" },
  { id_city: "BOS", name_city: "Boston, MA" },
  { id_city: "MIA", name_city: "Miami, FL" },
  { id_city: "ISP", name_city: "Islip, NY" },
  { id_city: "VPS", name_city: "Valparaiso, FL" },
  { id_city: "PBI", name_city: "West Palm Beach/Palm Beach, FL" },
  { id_city: "BLI", name_city: "Bellingham, WA" },
  { id_city: "MYR", name_city: "Myrtle Beach, SC" },
  { id_city: "FAT", name_city: "Fresno, CA" },
  { id_city: "HDN", name_city: "Hayden, CO" },
  { id_city: "ITO", name_city: "Hilo, HI" },
  { id_city: "JFK", name_city: "New York, NY" },
  { id_city: "EYW", name_city: "Key West, FL" },
  { id_city: "ORH", name_city: "Worcester, MA" },
  { id_city: "HPN", name_city: "White Plains, NY" },
  { id_city: "LEX", name_city: "Lexington, KY" },
  { id_city: "BGR", name_city: "Bangor, ME" },
  { id_city: "STT", name_city: "Charlotte Amalie, VI" },
  { id_city: "BQN", name_city: "Aguadilla, PR" },
  { id_city: "TLH", name_city: "Tallahassee, FL" },
  { id_city: "PSE", name_city: "Ponce, PR" },
  { id_city: "JAC", name_city: "Jackson, WY" },
  { id_city: "MSO", name_city: "Missoula, MT" },
  { id_city: "ANC", name_city: "Anchorage, AK" },
  { id_city: "DAB", name_city: "Daytona Beach, FL" },
  { id_city: "BIS", name_city: "Bismarck/Mandan, ND" },
  { id_city: "EGE", name_city: "Eagle, CO" },
  { id_city: "ATW", name_city: "Appleton, WI" },
  { id_city: "FAR", name_city: "Fargo, ND" },
  { id_city: "OAJ", name_city: "Jacksonville/Camp Lejeune, NC" },
  { id_city: "FCA", name_city: "Kalispell, MT" },
  { id_city: "GNV", name_city: "Gainesville, FL" },
  { id_city: "PSC", name_city: "Pasco/Kennewick/Richland, WA" },
  { id_city: "MLB", name_city: "Melbourne, FL" },
  { id_city: "CHA", name_city: "Chattanooga, TN" },
  { id_city: "TRI", name_city: "Bristol/Johnson City/Kingsport, TN" },
  { id_city: "STX", name_city: "Christiansted, VI" },
  { id_city: "FAI", name_city: "Fairbanks, AK" },
  { id_city: "FAY", name_city: "Fayetteville, NC" },
  { id_city: "TTN", name_city: "Trenton, NJ" },
  { id_city: "PGD", name_city: "Punta Gorda, FL" },
  { id_city: "SFB", name_city: "Sanford, FL" },
  { id_city: "AZA", name_city: "Phoenix, AZ" },
  { id_city: "ABE", name_city: "Allentown/Bethlehem/Easton, PA" },
  { id_city: "PVU", name_city: "Provo, UT" },
  { id_city: "PIE", name_city: "St. Petersburg, FL" },
  { id_city: "SMX", name_city: "Santa Maria, CA" },
  { id_city: "SBN", name_city: "South Bend, IN" },
  { id_city: "LCK", name_city: "Columbus, OH" },
  { id_city: "USA", name_city: "Concord, NC" },
  { id_city: "FWA", name_city: "Fort Wayne, IN" },
  { id_city: "MFR", name_city: "Medford, OR" },
  { id_city: "BLV", name_city: "Belleville, IL" },
  { id_city: "IAG", name_city: "Niagara Falls, NY" },
  { id_city: "HTS", name_city: "Ashland, WV" },
  { id_city: "STC", name_city: "St. Cloud, MN" },
  { id_city: "SWF", name_city: "Newburgh/Poughkeepsie, NY" },
  { id_city: "SCK", name_city: "Stockton, CA" },
  { id_city: "PBG", name_city: "Plattsburgh, NY" },
  { id_city: "RFD", name_city: "Rockford, IL" },
  { id_city: "HGR", name_city: "Hagerstown, MD" },
  { id_city: "SPI", name_city: "Springfield, IL" },
  { id_city: "PSM", name_city: "Portsmouth, NH" },
  { id_city: "BMI", name_city: "Bloomington/Normal, IL" },
  { id_city: "TOL", name_city: "Toledo, OH" },
  { id_city: "GFK", name_city: "Grand Forks, ND" },
  { id_city: "GRI", name_city: "Grand Island, NE" },
  { id_city: "GTF", name_city: "Great Falls, MT" },
  { id_city: "MRY", name_city: "Monterey, CA" },
  { id_city: "MOT", name_city: "Minot, ND" },
  { id_city: "EVV", name_city: "Evansville, IN" },
  { id_city: "CKB", name_city: "Clarksburg/Fairmont, WV" },
  { id_city: "ELM", name_city: "Elmira/Corning, NY" },
  { id_city: "PPG", name_city: "Pago Pago, TT" },
  { id_city: "MLU", name_city: "Monroe, LA" },
  { id_city: "COU", name_city: "Columbia, MO" },
  { id_city: "FSM", name_city: "Fort Smith, AR" },
  { id_city: "ACT", name_city: "Waco, TX" },
  { id_city: "SJT", name_city: "San Angelo, TX" },
  { id_city: "GRK", name_city: "Killeen, TX" },
  { id_city: "LAW", name_city: "Lawton/Fort Sill, OK" },
  { id_city: "MHK", name_city: "Manhattan/Ft. Riley, KS" },
  { id_city: "ABI", name_city: "Abilene, TX" },
  { id_city: "BPT", name_city: "Beaumont/Port Arthur, TX" },
  { id_city: "CLL", name_city: "College Station/Bryan, TX" },
  { id_city: "BFL", name_city: "Bakersfield, CA" },
  { id_city: "RST", name_city: "Rochester, MN" },
  { id_city: "HHH", name_city: "Hilton Head, SC" },
  { id_city: "LSE", name_city: "La Crosse, WI" },
  { id_city: "MGM", name_city: "Montgomery, AL" },
  { id_city: "CMI", name_city: "Champaign/Urbana, IL" },
  { id_city: "SBP", name_city: "San Luis Obispo, CA" },
  { id_city: "AGS", name_city: "Augusta, GA" },
  { id_city: "ACY", name_city: "Atlantic City, NJ" },
  { id_city: "LBE", name_city: "Latrobe, PA" },
  { id_city: "CRW", name_city: "Charleston/Dunbar, WV" },
  { id_city: "LAN", name_city: "Lansing, MI" },
  { id_city: "RDM", name_city: "Bend/Redmond, OR" },
  { id_city: "PRC", name_city: "Prescott, AZ" },
  { id_city: "GCC", name_city: "Gillette, WY" },
  { id_city: "DVL", name_city: "Devils Lake, ND" },
  { id_city: "JMS", name_city: "Jamestown, ND" },
  { id_city: "MCW", name_city: "Mason City, IA" },
  { id_city: "FOD", name_city: "Fort Dodge, IA" },
  { id_city: "MBS", name_city: "Saginaw/Bay City/Midland, MI" },
  { id_city: "HLN", name_city: "Helena, MT" },
  { id_city: "LWS", name_city: "Lewiston, ID" },
  { id_city: "RDD", name_city: "Redding, CA" },
  { id_city: "LBF", name_city: "North Platte, NE" },
  { id_city: "HYS", name_city: "Hays, KS" },
  { id_city: "SLN", name_city: "Salina, KS" },
  { id_city: "DEC", name_city: "Decatur, IL" },
  { id_city: "JLN", name_city: "Joplin, MO" },
  { id_city: "CMX", name_city: "Hancock/Houghton, MI" },
  { id_city: "SGU", name_city: "St. George, UT" },
  { id_city: "DDC", name_city: "Dodge City, KS" },
  { id_city: "CYS", name_city: "Cheyenne, WY" },
  { id_city: "JST", name_city: "Johnstown, PA" },
  { id_city: "MEI", name_city: "Meridian, MS" },
  { id_city: "SUX", name_city: "Sioux City, IA" },
  { id_city: "RIW", name_city: "Riverton/Lander, WY" },
  { id_city: "RKS", name_city: "Rock Springs, WY" },
  { id_city: "VEL", name_city: "Vernal, UT" },
  { id_city: "SUN", name_city: "Sun Valley/Hailey/Ketchum, ID" },
  { id_city: "ASE", name_city: "Aspen, CO" },
  { id_city: "BIH", name_city: "Bishop, CA" },
  { id_city: "ACV", name_city: "Arcata/Eureka, CA" },
  { id_city: "SHR", name_city: "Sheridan, WY" },
  { id_city: "LAR", name_city: "Laramie, WY" },
  { id_city: "XWA", name_city: "Williston, ND" },
  { id_city: "PIB", name_city: "Hattiesburg/Laurel, MS" },
  { id_city: "DLH", name_city: "Duluth, MN" },
  { id_city: "BFF", name_city: "Scottsbluff, NE" },
  { id_city: "VCT", name_city: "Victoria, TX" },
  { id_city: "CNY", name_city: "Moab, UT" },
  { id_city: "DIK", name_city: "Dickinson, ND" },
  { id_city: "ALW", name_city: "Walla Walla, WA" },
  { id_city: "SPS", name_city: "Wichita Falls, TX" },
  { id_city: "STS", name_city: "Santa Rosa, CA" },
  { id_city: "AZO", name_city: "Kalamazoo, MI" },
  { id_city: "FLG", name_city: "Flagstaff, AZ" },
  { id_city: "TYR", name_city: "Tyler, TX" },
  { id_city: "AEX", name_city: "Alexandria, LA" },
  { id_city: "YUM", name_city: "Yuma, AZ" },
  { id_city: "CSG", name_city: "Columbus, GA" },
  { id_city: "BQK", name_city: "Brunswick, GA" },
  { id_city: "ABY", name_city: "Albany, GA" },
  { id_city: "INL", name_city: "International Falls, MN" },
  { id_city: "HIB", name_city: "Hibbing, MN" },
  { id_city: "ABR", name_city: "Aberdeen, SD" },
  { id_city: "ESC", name_city: "Escanaba, MI" },
  { id_city: "TXK", name_city: "Texarkana, AR" },
  { id_city: "GGG", name_city: "Longview, TX" },
  { id_city: "ROW", name_city: "Roswell, NM" },
  { id_city: "RHI", name_city: "Rhinelander, WI" },
  { id_city: "BJI", name_city: "Bemidji, MN" },
  { id_city: "BTM", name_city: "Butte, MT" },
  { id_city: "TWF", name_city: "Twin Falls, ID" },
  { id_city: "CIU", name_city: "Sault Ste. Marie, MI" },
  { id_city: "PLN", name_city: "Pellston, MI" },
  { id_city: "BRD", name_city: "Brainerd, MN" },
  { id_city: "CDC", name_city: "Cedar City, UT" },
  { id_city: "APN", name_city: "Alpena, MI" },
  { id_city: "GCK", name_city: "Garden City, KS" },
  { id_city: "IMT", name_city: "Iron Mountain/Kingsfd, MI" },
  { id_city: "SWO", name_city: "Stillwater, OK" },
  { id_city: "PIH", name_city: "Pocatello, ID" },
  { id_city: "EKO", name_city: "Elko, NV" },
  { id_city: "OTH", name_city: "North Bend/Coos Bay, OR" },
  { id_city: "LBL", name_city: "Liberal, KS" },
  { id_city: "GUM", name_city: "Guam, TT" },
  { id_city: "SPN", name_city: "Saipan, TT" },
  { id_city: "DHN", name_city: "Dothan, AL" },
  { id_city: "GTR", name_city: "Columbus, MS" },
  { id_city: "CWA", name_city: "Mosinee, WI" },
  { id_city: "MQT", name_city: "Marquette, MI" },
  { id_city: "VLD", name_city: "Valdosta, GA" },
  { id_city: "BGM", name_city: "Binghamton, NY" },
  { id_city: "EWN", name_city: "New Bern/Morehead/Beaufort, NC" },
  { id_city: "ERI", name_city: "Erie, PA" },
  { id_city: "ART", name_city: "Watertown, NY" },
  { id_city: "PGV", name_city: "Greenville, NC" },
  { id_city: "PHF", name_city: "Newport News/Williamsburg, VA" },
  { id_city: "SBY", name_city: "Salisbury, MD" },
  { id_city: "FLO", name_city: "Florence, SC" },
  { id_city: "LYH", name_city: "Lynchburg, VA" },
  { id_city: "ALO", name_city: "Waterloo, IA" },
  { id_city: "KTN", name_city: "Ketchikan, AK" },
  { id_city: "SIT", name_city: "Sitka, AK" },
  { id_city: "JNU", name_city: "Juneau, AK" },
  { id_city: "PAE", name_city: "Everett, WA" },
  { id_city: "BET", name_city: "Bethel, AK" },
  { id_city: "BRW", name_city: "Barrow, AK" },
  { id_city: "SCC", name_city: "Deadhorse, AK" },
  { id_city: "YAK", name_city: "Yakutat, AK" },
  { id_city: "CDV", name_city: "Cordova, AK" },
  { id_city: "PSG", name_city: "Petersburg, AK" },
  { id_city: "WRG", name_city: "Wrangell, AK" },
  { id_city: "ADQ", name_city: "Kodiak, AK" },
  { id_city: "OME", name_city: "Nome, AK" },
  { id_city: "OTZ", name_city: "Kotzebue, AK" },
  { id_city: "ADK", name_city: "Adak Island, AK" },
  { id_city: "YKM", name_city: "Yakima, WA" },
  { id_city: "PUW", name_city: "Pullman, WA" },
  { id_city: "EAT", name_city: "Wenatchee, WA" },
  { id_city: "DLG", name_city: "Dillingham, AK" },
  { id_city: "AKN", name_city: "King Salmon, AK" },
];

const initialForm: FlightForm = {
  origin: CITIES[0].id_city,
  destination: CITIES[2].id_city,
  scheduled_departure: getRoundedHourFormatted(),
};

export default function App() {
  const [form, setForm] = useState<FlightForm>(initialForm);
  const [response, setResponse] = useState<PredictData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const set = (key: keyof FlightForm) => (val: string) =>
    setForm((f) => ({ ...f, [key]: val }));

  const handleSubmit = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    setResponse(null);

    const payload = {
      ...form,
      scheduled_departure: form.scheduled_departure + ":00",
    };

    try {
      const res = await fetch("/api/predict/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Erreur ${res.status} : ${res.statusText}`);

      const data = (await res.json()) as PredictData;
      console.log("data brut :", data);

      setResponse(data);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Une erreur est survenue");
      }
    } finally {
      setLoading(false);
    }
  };

  const now = new Date();
  const maxDate = new Date();
  maxDate.setDate(now.getDate() + 15);

  const formatDate = (date: Date) => {
    return date.toISOString().slice(0, 16);
  };
  console.log({ response });
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <svg
            className="w-4 h-4 text-white"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </div>
        <div>
          <h1 className="text-sm font-bold text-gray-900">
            Flight Delay Predictor
          </h1>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-10 space-y-6">
        {/* Formulaire */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
          <h2 className="text-base font-bold text-gray-900 mb-1">
            Paramètres du vol
          </h2>
          <p className="text-sm text-gray-400 mb-6">
            Renseigne les informations pour lancer la prédiction.
          </p>

          <div className="grid grid-cols-2 gap-4 mb-6">
            {/* Origine */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-1.5">
                Origine
              </label>
              <select
                value={form.origin}
                onChange={(e) => set("origin")(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition bg-white"
              >
                {CITIES.filter((c) => c.id_city !== form.destination).map(
                  (c) => (
                    <option key={c.id_city} value={c.id_city}>
                      {c.name_city} ({c.id_city})
                    </option>
                  ),
                )}
              </select>
            </div>

            {/* Destination */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-1.5">
                Destination
              </label>
              <select
                value={form.destination}
                onChange={(e) => set("destination")(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition bg-white"
              >
                {CITIES.filter((c) => c.id_city !== form.origin).map((c) => (
                  <option key={c.id_city} value={c.id_city}>
                    {c.name_city} ({c.id_city})
                  </option>
                ))}
              </select>
            </div>

            {/* Date */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-1.5">
                Départ prévu
              </label>
              <input
                type="datetime-local"
                value={form.scheduled_departure}
                min={formatDate(now)}
                max={formatDate(maxDate)}
                onChange={(e) => set("scheduled_departure")(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition bg-white"
              />
            </div>
          </div>

          <ButtonCustom onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <>
                <svg
                  className="animate-spin w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
                Analyse en cours…
              </>
            ) : (
              "Lancer la prédiction"
            )}
          </ButtonCustom>

          {/* Erreur */}
          {error !== null && (
            <div className="mt-4 flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              <svg
                className="w-4 h-4 text-red-500 mt-0.5 shrink-0"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                />
              </svg>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
        </div>

        {response !== null && (
          <ViewPredict
            dataPredict={response}
            onclick={() => setResponse(null)}
          />
        )}
      </main>
    </div>
  );
}
