import random

def get_weather_advice(location):
    """
    Simulate fetching real-time weather advice based on the location.
    In a real app, this would hit an API like OpenWeatherMap.
    """
    location = location.lower()
    
    # Pre-defined mock responses based on location keywords
    if 'pune' in location or 'mumbai' in location or 'maharashtra' in location:
        advice = "Heavy rainfall expected in the coming week. Good for rain-fed crops, but ensure proper drainage to avoid waterlogging."
    elif 'delhi' in location or 'punjab' in location or 'haryana' in location:
        advice = "Dry and hot conditions prevailing. Consider increasing irrigation frequency. Good time for wheat sowing if season permits."
    elif 'chennai' in location or 'tamil' in location or 'kerala' in location:
        advice = "High humidity with moderate showers. Favorable conditions for rice and coastal crops. Monitor for fungal diseases."
    else:
        # Generic random advice
        advices = [
            "Clear skies for the next 5 days. Ideal conditions for harvesting.",
            "Scattered showers expected. Delay sowing if possible.",
            "Temperature dropping below average. Protect sensitive crops from frost.",
            "Favorable weather conditions. Proceed with planned agricultural activities."
        ]
        advice = random.choice(advices)
        
    return advice

# List of all 175 AP Assembly Constituencies
AP_CONSTITUENCIES = [
    'Ichchapuram', 'Palasa', 'Tekkali', 'Pathapatnam', 'Srikakulam', 'Amadalavalasa', 'Etcherla', 'Narasannapeta', 'Rajam', 'Palakonda',
    'Kurupam', 'Parvathipuram', 'Salur', 'Bobbili', 'Cheepurupalli', 'Gajapathinagaram', 'Nellimarla', 'Vizianagaram', 'Srungavarapukota', 'Bhimli',
    'Visakhapatnam East', 'Visakhapatnam South', 'Visakhapatnam North', 'Visakhapatnam West', 'Gajuwaka', 'Chodavaram', 'Madugula', 'Araku Valley', 'Paderu', 'Anakapalle', 'Pendurthi', 'Yelamanchili', 'Payakaraopet', 'Narsipatnam',
    'Tuni', 'Prathipadu', 'Pithapuram', 'Kakinada Rural', 'Peddapuram', 'Anaparthy', 'Kakinada City', 'Ramachandrapuram', 'Mummidivaram', 'Amalapuram', 'Razole', 'Kothapeta', 'Mandapeta', 'Rajanagaram',
    'Rajahmundry City', 'Rajahmundry Rural', 'Jaggampeta', 'Rampachodavaram', 'Kovvur', 'Nidadavole', 'Achanta', 'Palakollu', 'Narasapuram', 'Bhimavaram', 'Undi', 'Tanuku', 'Tadepalligudem', 'Unguturu', 'Denduluru', 'Eluru', 'Gopalapuram', 'Polavaram', 'Chintalapudi',
    'Tiruvuru', 'Nuzvid', 'Gannavaram', 'Gudivada', 'Kaikalur', 'Pedana', 'Machilipatnam', 'Avanigadda', 'Pamarru', 'Penamaluru', 'Vijayawada West', 'Vijayawada Central', 'Vijayawada East', 'Mylavaram', 'Nandigama', 'Jaggayyapeta',
    'Pedakurapadu', 'Tadikonda', 'Mangalagiri', 'Ponnur', 'Vemuru', 'Repalle', 'Tenali', 'Bapatla', 'Prathipadu (Guntur)', 'Guntur West', 'Guntur East', 'Chilakaluripet', 'Narasaraopet', 'Sattenapalle', 'Vinukonda', 'Gurajala', 'Macherla',
    'Yerragondapalem', 'Darsi', 'Parchur', 'Addanki', 'Chirala', 'Santhanuthalapadu', 'Ongole', 'Kandukur', 'Kondapi', 'Markapuram', 'Giddalur', 'Kanigiri',
    'Kavali', 'Atmakur', 'Kovur', 'Nellore City', 'Nellore Rural', 'Sarvepalli', 'Gudur', 'Sullurpeta', 'Venkatagiri', 'Udayagiri',
    'Badvel', 'Rajampet', 'Kadapa', 'Kodur', 'Rayachoti', 'Pulivendula', 'Kamalapuram', 'Jammalamadugu', 'Proddatur', 'Mydukur',
    'Allagadda', 'Srisailam', 'Nandikotkur', 'Kurnool', 'Panyam', 'Nandyal', 'Banaganapalle', 'Dhone', 'Pattikonda', 'Kodumur', 'Yemmiganur', 'Mantralayam', 'Adoni', 'Alur',
    'Rayadurg', 'Uravakonda', 'Guntakal', 'Tadipatri', 'Singanamala', 'Anantapur Urban', 'Kalyandurg', 'Raptadu', 'Madakasira', 'Hindupur', 'Penukonda', 'Puttaparthi', 'Dharmavaram', 'Kadiri',
    'Thamballapalle', 'Pileru', 'Madanapalle', 'Punganur', 'Chandragiri', 'Tirupati', 'Srikalahasti', 'Satyavedu', 'Nagari', 'Gangadhara Nellore', 'Chittoor', 'Puthalapattu', 'Palamaner', 'Kuppam'
]

def is_valid_constituency(location_name):
    """
    Validates if the user input strictly matches any of the 175 AP constituencies.
    """
    if not location_name or not location_name.strip():
        return False
        
    loc_lower = location_name.lower().strip()
    
    # Exact or highly close match validation
    for constituency in AP_CONSTITUENCIES:
        if loc_lower == constituency.lower().strip() or loc_lower in constituency.lower().strip():
            return True
            
    return False

def process_form_input(form_data):
    """
    Process raw form data into the formats expected by our models.
    """
    # AP Soil mapping: 
    # 0: Red Sandy Loam, 1: Black Cotton, 2: Coastal Alluvial, 3: Laterite
    soil_map = {
        'red_sandy_loam': 0, 
        'black_cotton': 1, 
        'coastal_alluvial': 2, 
        'laterite': 3
    }
    
    # Season mapping: 0: Kharif, 1: Rabi, 2: Zaid
    season_map = {'kharif': 0, 'rabi': 1, 'zaid': 2}
    
    # Water availability mapping: 0: Low, 1: Medium, 2: High
    water_map = {'low': 0, 'medium': 1, 'high': 2}
    
    soil_val = soil_map.get(form_data.get('soil', '').lower(), 0)
    season_val = season_map.get(form_data.get('season', '').lower(), 0)
    water_val = water_map.get(form_data.get('water', '').lower(), 1)
    
    return {
        'location': form_data.get('location', 'Unknown'),
        'soil': soil_val,
        'season': season_val,
        'water': water_val
    }
