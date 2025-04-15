import pandas as pd
from bs4 import BeautifulSoup
import re

html_file_path = "final_project/seoeun_followers.html"
csv_file_path = "final_project/seoeun_followers_data.csv"
base_instagram_url = "https://www.instagram.com"

def extract_username_from_alt(alt_text):
    """Extracts username from image alt text like \"username's profile picture\""""
    if not alt_text:
        return None
    match = re.match(r"^(.*?)'s profile picture$", alt_text)
    return match.group(1) if match else None

def scrape_followers(html_path):
    """Scrapes follower data from the saved HTML file."""
    followers_data = []
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_path}")
        return None

    potential_follower_divs = soup.find_all("div", class_="x1dm5mii") 
    
    if not potential_follower_divs:
         print("Primary selector 'div.x1dm5mii' not found.")
         username_links = soup.select('a[href^="/"][href$="/"] span._ap3a')
         potential_follower_divs = [link.find_parent("div", class_="x1dm5mii") for link in username_links if link.find_parent("div", class_="x1dm5mii")]
         #remove duplicates if any found
         potential_follower_divs = list(dict.fromkeys(potential_follower_divs))


    print(f"Found {len(potential_follower_divs)} potential follower entries.")

    for follower_div in potential_follower_divs:
        username = None
        full_name = None
        profile_url = None
        img_url = None
        
        #username span
        username_link_tag = follower_div.find("a", href=re.compile(r"^/[^/]+/$"), role="link", tabindex="0")
        if username_link_tag:
            href = username_link_tag.get("href")
            if href:
                profile_url = base_instagram_url + href
                username_span = username_link_tag.find("span", class_="_ap3a") #May edit
                if username_span and username_span.text:
                     username = username_span.text.strip()
                elif len(href) > 2:
                     username = href.strip('/')

        try:
            username_container_div = follower_div.find("div", class_="x1rg5ohu") #may need to change
            if username_container_div:
                 full_name_outer_span = username_container_div.find_next_sibling("span")
                 if full_name_outer_span:
                      full_name_inner_span = full_name_outer_span.find("span", class_="x1lliihq") #may need to edit
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
                if not profile_url:
                     profile_url = base_instagram_url + f"/{username}/"

        if username and profile_url:
             followers_data.append({
                 "username": username,
                 "full_name": full_name if full_name else "",
                 "profile_url": profile_url,
                 "image_url": img_url if img_url else ""
             })


    if not followers_data:
        print("Warning: No follower data was successfully extracted. Check HTML structure and selectors.")
        return None
        
        #CSV
    df = pd.DataFrame(followers_data)
    
    try:
        df.to_csv(csv_file_path, index=False, encoding="utf-8")
        print(f"Successfully scraped {len(df)} followers to {csv_file_path}")
    except Exception as e:
        print(f"Error saving DataFrame to CSV: {e}")
        return None
        
    return df

def main():
    scraped_df = scrape_followers(html_file_path)
    if scraped_df is not None:
        print("\n--- first 5 rows ---")
        print(scraped_df.head())
        print("\n--- df info ---")
        scraped_df.info()

if __name__ == "__main__":
    main()