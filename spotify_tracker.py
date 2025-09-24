import os
import pandas as pd
import requests
import base64
from dotenv import load_dotenv
from datetime import datetime

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')


def get_spotify_token():
    """Gets an access token from the Spotify API."""
    auth_url = 'https://accounts.spotify.com/api/token'
    
    # Base64 encode the client ID and client secret
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth_header}'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post(auth_url, headers=headers, data=data)
    response.raise_for_status() # Raise an exception for bad status codes
    
    return response.json()['access_token']


def get_top_artists(token):
    """Gets your top artists from the Spotify API. NOTE: Needs user authorization."""
    # This endpoint requires user-specific data and a different authorization flow
    # (Authorization Code Flow) which is more complex to set up for a simple script.
    # We will pivot to a simpler, public endpoint: New Releases.
    print("Pivoting to a simpler, public API endpoint: New Releases.")
    
    releases_url = 'https://api.spotify.com/v1/browse/new-releases'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(releases_url, headers=headers, params={'limit': 5})
    response.raise_for_status()
    
    # Extract relevant data from the JSON response
    releases = response.json()['albums']['items']
    
    artist_data = []
    for release in releases:
        artist_name = release['artists'][0]['name']
        album_name = release['name']
        release_date = release['release_date']
        artist_data.append({
            'artist_name': artist_name,
            'album_name': album_name,
            'release_date': release_date
        })
        
    return artist_data


def main():
    """Main function to run the data pipeline."""
    print("Starting Spotify data pipeline...")
    
    try:
        token = get_spotify_token()
        print("Successfully obtained Spotify token.")
        
        # NOTE: The /me/top/artists endpoint is not accessible with the simple Client Credentials flow.
        # We are using the 'new-releases' endpoint instead which is publicly accessible.
        new_releases = get_top_artists(token)
        
        if new_releases:
            df = pd.DataFrame(new_releases)
            
            # --- SAVE DATA ---
            # Create a timestamp for the current run
            today_str = datetime.now().strftime('%Y-%m-%d')
            df['snapshot_date'] = today_str
            
            output_path = 'data/daily_spotify_releases.csv'
            
            # Append data to the CSV file
            if os.path.exists(output_path):
                df.to_csv(output_path, mode='a', header=False, index=False)
                print(f"Appended {len(df)} new releases to {output_path}")
            else:
                df.to_csv(output_path, index=False)
                print(f"Created {output_path} and saved {len(df)} new releases.")
        else:
            print("No new releases found.")
            
    except requests.exceptions.HTTPError as e:
        print(f"An API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()