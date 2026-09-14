all_products = [
    "categorize",
    "classification",
    "der",
    "disdrometer",
    "doppler-lidar",
    "doppler-lidar-wind",
    "drizzle",
    "epsilon-lidar",
    "ier",
    "iwc",
    "lidar",
    "lwc",
    "mwr-l1c",
    "mwr-multi",
    "mwr-single",
    "radar",
    "rain-gauge",
    "weather-station",
]

instrument_products = [
    "disdrometer",
    "doppler-lidar",
    "doppler-lidar-wind",
    "epsilon-lidar",
    "lidar",
    "mwr-l1c",
    "mwr-single",
    "mwr-multi",
    "radar",
    "rain-gauge",
    "weather-station",
]

geophysical_products = [
    "categorize",
    "classification",
    "der",
    "drizzle",
    "ier",
    "iwc",
    "lwc",
]

products_to_plot = [
    "lidar",
    "mwr-l1c",
    "mwr-single",
    "radar",
    "disdrometer",
    "categorize",
    "classification",
]

lsize, asize, tsize = 12, 14, 16

url_instrument = "https://cloudnet.fmi.fi/api/files?site={site}&dateFrom={date_start}&dateTo={date_end}&product={product}&instrumentPid={pid}"
url_geophysical = "https://cloudnet.fmi.fi/api/files?site={site}&dateFrom={date_start}&dateTo={date_end}&product={product}"
