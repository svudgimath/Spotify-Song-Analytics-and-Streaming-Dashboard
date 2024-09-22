import requests
import base64
import time
import pandas as pd

# Step 1: Spotify API credentials
client_id = ''  # Replace with your Client ID
client_secret = ''  # Replace with your Client Secret
redirect_uri = 'https://example.com/callback'  # Your Redirect URI

# Step 2: Get Spotify API access token
def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    
    # Create base64 encoded client credentials
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(auth_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        return token
    else:
        raise Exception(f"Failed to get token: {response.status_code}, {response.text}")

# Step 3: Function to get Spotify album cover image URL
def get_spotify_album_image_url(token, track_name, artist_name, max_retries=3, retry_delay=5):
    search_url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'q': f'track:{track_name} artist:{artist_name}',
        'type': 'track',
        'limit': 1
    }
    
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['tracks']['items']:
                    album_info = data['tracks']['items'][0]['album']
                    # Return the URL of the album cover image
                    return album_info['images'][0]['url'] if album_info['images'] else None
                else:
                    return None  # Return None if no track is found
            else:
                raise Exception(f"Failed to fetch track: {response.status_code}, {response.text}")
        except requests.exceptions.Timeout:
            print(f"Timeout occurred, retrying... (Attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            print(f"Error fetching track: {e}")
        
        # Increment attempt and wait before retrying
        attempt += 1
        time.sleep(retry_delay)

    return None  # Return None if failed after retries

# Step 4: Fetch album cover URLs for tracks in the dataset
def fetch_spotify_album_image_urls(dataframe):
    token = get_spotify_token(client_id, client_secret)
    
    image_urls = []
    
    for index, row in dataframe.iterrows():
        print(f"Fetching album image for track: {row['track_name']} by {row['artist(s)_name']}")
        album_image_url = get_spotify_album_image_url(token, row['track_name'], row['artist(s)_name'])
        if album_image_url:
            image_urls.append(album_image_url)
        else:
            print(f"Skipping track: {row['track_name']} - Album image not found")
            image_urls.append(None)  # Append None if the album image is not found
    
    dataframe['album_image_url'] = image_urls
    return dataframe

# Load your dataset
file_path = 'spotify.csv'  # Update this path if necessary
spotify_data = pd.read_csv(file_path, encoding='ISO-8859-1')

# Step 5: Fetch Spotify album cover image URLs for the tracks in the entire dataset
updated_data = fetch_spotify_album_image_urls(spotify_data)

# Display the updated dataframe with Album Image URLs
print(updated_data[['track_name', 'artist(s)_name', 'album_image_url']].head())

# Save the updated data with Album Image URLs
output_file_path = 'spotifyimages.csv'
updated_data.to_csv(output_file_path, index=False)

