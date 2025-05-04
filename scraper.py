import pandas as pd
from bs4 import BeautifulSoup
import re
import os

#configuration
html_dir = "html_files"
csv_dir = "csv_files"
base_instagram_url = "https://www.instagram.com"

def extract_username_from_alt(alt_text):
    """Extracts username from image alt text like \"username's profile picture\""""
    if not alt_text:
        return None
    match = re.match(r"^(.*?)'s profile picture$", alt_text)
    return match.group(1) if match else None

def scrape_followers(html_path, csv_output_path):
    """Scrapes follower data from the saved HTML file and saves to CSV."""
    print(f"--- Processing: {os.path.basename(html_path)} ---")
    followers_data = []
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_path}")
        return None
    except Exception as e:
        print(f"Error reading or parsing HTML file {html_path}: {e}")
        return None

    # Find the main container divs for each follower
    potential_follower_divs = soup.find_all("div", class_="x1dm5mii") 
    
    if not potential_follower_divs:
         # Fallback logic remains the same
         print("Primary selector 'div.x1dm5mii' not found. Trying fallback based on username links.")
         username_links = soup.select('a[href^="/"][href$="/"] span._ap3a') # Select spans within profile links
         potential_follower_divs = [link.find_parent("div", class_="x1dm5mii") for link in username_links if link.find_parent("div", class_="x1dm5mii")]
         potential_follower_divs = list(dict.fromkeys(potential_follower_divs)) # Remove duplicates


    print(f"Found {len(potential_follower_divs)} potential follower entries.")

    for follower_div in potential_follower_divs:
        # Reset variables for each follower
        username = None
        full_name = None
        profile_url = None
        img_url = None
        
        username_link_tag = follower_div.find("a", href=re.compile(r"^/[^/]+/$"), role="link", tabindex="0")
        if username_link_tag:
            href = username_link_tag.get("href")
            if href:
                profile_url = base_instagram_url + href
                username_span = username_link_tag.find("span", class_="_ap3a") # Class might change!
                if username_span and username_span.text:
                     username = username_span.text.strip()
                elif len(href) > 2:
                     username = href.strip('/') # Fallback to username from href

        # --- Extract Full Name ---
        try:
            full_name_span = follower_div.find("span", class_="x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft")
            if full_name_span:
                 full_name = full_name_span.text.strip()
            else:
                 # Fallback: Try finding the outer span structure if the inner one fails
                 full_name_outer_span = follower_div.find("span", class_="x1lliihq x1plvlek xryxfnj") # This outer class might be more stable
                 if full_name_outer_span:
                     full_name_inner_span = full_name_outer_span.find("span", class_="x1lliihq") # Find any inner span
                     if full_name_inner_span:
                         full_name = full_name_inner_span.text.strip()
                                    
        except Exception as e:
            pass 

        img_tag = follower_div.find("img", class_="xpdipgo") #may need to edit
        if img_tag:
            img_url = img_tag.get("src")
            alt_text = img_tag.get("alt")
            alt_username = extract_username_from_alt(alt_text)
            if not username and alt_username: 
                username = alt_username
                if not profile_url and username: 
                     profile_url = base_instagram_url + f"/{username}/"

        if username and profile_url: # Only add if we have the essentials
             followers_data.append({
                 "username": username,
                 "full_name": full_name if full_name else "", # Use empty string if None
                 "profile_url": profile_url,
                 "image_url": img_url if img_url else ""    # Use empty string if None
             })
        # else:
             # Optional debug log for skipped entries
             # print(f"Skipping entry, missing username or profile URL.")


    if not followers_data:
        print("Warning: No follower data was successfully extracted. Check HTML structure and selectors.")
        return None
        
    df = pd.DataFrame(followers_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)

    try:
        df.to_csv(csv_output_path, index=False, encoding="utf-8")
        print(f"Successfully scraped {len(df)} followers to {os.path.basename(csv_output_path)}")
    except Exception as e:
        print(f"Error saving DataFrame to CSV {csv_output_path}: {e}")
        return None
        
    return df

def main():
    # Ensure output directory exists before starting
    os.makedirs(csv_dir, exist_ok=True)
    
    print(f"Starting scraper. Input HTML directory: {html_dir}, Output CSV directory: {csv_dir}")
    
    processed_files = 0
    # Loop through files in the html directory
    for filename in os.listdir(html_dir):
        if filename.endswith(".html"):
            current_html_path = os.path.join(html_dir, filename)
            base_name = os.path.splitext(filename)[0]
            current_csv_path = os.path.join(csv_dir, f"{base_name}_data.csv")
            
            scraped_df = scrape_followers(current_html_path, current_csv_path)
            
            if scraped_df is not None:
                processed_files += 1
                # Optionally print head/info for each processed file
                # print(f"\\n--- First 5 rows for {filename} ---")
                # print(scraped_df.head())
                # print(f"\\n--- DataFrame Info for {filename} ---")
                # scraped_df.info()
            print("-" * 30) 

    print(f"Finished scraping. Processed {processed_files} HTML files.")

if __name__ == "__main__":
    main()