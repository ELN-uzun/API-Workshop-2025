# Importieren der notwendigen Bibliothek für den Zugriff auf die eLabFTW API
import elabapi_python
import urllib3

# Warnungen bei Self-signed-Zertifikaten deaktivieren (optional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Konfiguration
API_HOST_URL = 'https://host-url/api/v2'  # Deine API URL
API_KEY = 'your-api-key'  # Dein API-Key

# API-Client konfigurieren
configuration = elabapi_python.Configuration()
configuration.api_key['api_key'] = API_KEY  # Setzen des API-Schlüssels für die Authentifizierung
configuration.api_key_prefix['api_key'] = 'Authorization'  # Festlegen des Prefix für den Header
configuration.host = API_HOST_URL  # Die Basis-URL der API
configuration.debug = False  # Debugging deaktivieren (optional)
configuration.verify_ssl = True  # SSL-Zertifikat überprüfen (wichtig für sichere Kommunikation)

# Erstellen des API-Clients mit der oben genannten Konfiguration
api_client = elabapi_python.ApiClient(configuration)
api_client.set_default_header(header_name='Authorization', header_value=API_KEY)  # Setzen des Authorization-Headers

# API-Instanz für die Abrufung der Kategorien (ItemsTypes) erstellen
items_api = elabapi_python.ItemsTypesApi(api_client)

# API-Instanz für die Abrufung der Items (Einträge) pro Kategorie erstellen
items_api2 = elabapi_python.ItemsApi(api_client)

try:
    # Abrufen der Kategorien (ItemsTypes) von der API
    item_types = items_api.read_items_types()  # Alle Kategorien werden abgefragt

    # Ausgabe der Anzahl der Kategorien
    print(f"Anzahl der Kategorien: {len(item_types)}")

    # Durchlaufen der Kategorien und Ausgabe von ID und Titel jeder Kategorie
    for item_type in item_types:
        print(f"ID: {item_type.id}, Titel: {item_type.title}")

        # Abrufen der Items (Einträge) für jede Kategorie anhand der ID
        entries = items_api2.read_items(cat=item_type.id,
                                        limit=100)  # Hier wird die Anzahl der Items in der Kategorie abgerufen
        entry_count = len(entries)  # Zählen der Items

        # Ausgabe der Anzahl der Items in der aktuellen Kategorie
        print(f"Anzahl der Einträge in dieser Kategorie: {entry_count}\n")

# Fehlerbehandlung für API-Anfragen
except elabapi_python.rest.ApiException as e:
    print(f"Fehler beim Abrufen der Kategorien oder Einträge: {e}")
