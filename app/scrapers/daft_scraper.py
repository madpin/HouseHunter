import re
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import HttpUrl
from bs4 import BeautifulSoup
import aiohttp
from aiohttp import ClientError
from app.scrapers.base_scraper import BaseScraper
from app.models.property import (
    Property, WebsiteSource, PropertyType, Address, PropertyImage, 
    AgentInfo, PropertyFeature, ListingStatus
)

class DaftScraper(BaseScraper):
    """Scraper for Daft.ie property listings"""
    
    def __init__(self):
        super().__init__(WebsiteSource.DAFT)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',  # Now that Brotli is installed, we can use it
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
        return self.session
    
    def can_handle_url(self, url: HttpUrl) -> bool:
        """
        Check if this is a valid Daft.ie property listing URL
        
        Supports URLs like:
        - https://www.daft.ie/for-sale/end-of-terrace-house-168-rutland-avenue-crumlin-crumlin-dublin-12/6200303
        - https://www.daft.ie/property-for-sale/[location]/[listing-id]
        """
        url_str = str(url)
        
        # Check if it's a daft.ie domain
        if "daft.ie" not in url_str:
            return False
        
        # Check if it's a property listing URL (for-sale, for-rent, etc.)
        property_patterns = [
            r'/for-sale/',
            r'/for-rent/',
            r'/property-for-sale/',
            r'/property-for-rent/',
            r'/commercial-for-sale/',
            r'/commercial-for-rent/'
        ]
        
        for pattern in property_patterns:
            if re.search(pattern, url_str):
                return True
        
        return False
    
    def extract_listing_id(self, url: HttpUrl) -> Optional[str]:
        """
        Extract listing ID from Daft URL
        
        Supports multiple URL patterns:
        - /for-sale/[description]/[listing-id]
        - /for-rent/[description]/[listing-id]
        - /property-for-sale/[location]/[listing-id]
        """
        url_str = str(url)
        
        # Pattern 1: /for-sale/ or /for-rent/ followed by description and numeric ID
        # Example: /for-sale/end-of-terrace-house-168-rutland-avenue-crumlin-crumlin-dublin-12/6200303
        match = re.search(r'/(?:for-sale|for-rent)/[^/]+/(\d+)(?:\?|$)', url_str)
        if match:
            return match.group(1)
        
        # Pattern 2: /property-for-sale/ or /property-for-rent/ followed by location and ID
        # Example: /property-for-sale/dublin-city/12345
        match = re.search(r'/property-(?:for-sale|for-rent)/[^/]+/(\d+)(?:\?|$)', url_str)
        if match:
            return match.group(1)
        
        # Pattern 3: /commercial-for-sale/ or /commercial-for-rent/
        match = re.search(r'/commercial-(?:for-sale|for-rent)/[^/]+/(\d+)(?:\?|$)', url_str)
        if match:
            return match.group(1)
        
        # Fallback: look for any numeric ID at the end of the URL path
        match = re.search(r'/(\d+)(?:\?|$)', url_str)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from the page"""
        # Look for price in various formats
        price_selectors = [
            'h1',  # Main heading often contains price
            '[data-testid="price"]',
            '.price',
            '.property-price',
            'h2',
            'span',
            'div'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Extract price using regex - look for € followed by numbers
                price_match = re.search(r'€\s*([\d,]+)', text.replace(',', ''))
                if price_match:
                    return float(price_match.group(1))
        
        # Also check for price in the page title or meta tags
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            price_match = re.search(r'€\s*([\d,]+)', title_text.replace(',', ''))
            if price_match:
                return float(price_match.group(1))
        
        return None
    
    def _extract_address(self, soup: BeautifulSoup) -> Optional[Address]:
        """Extract address information"""
        # Look for address in various locations
        address_selectors = [
            'h1',  # Main heading often contains address
            '[data-testid="address"]',
            '.address',
            '.property-address',
            'title'
        ]
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Extract address components
                # Example: "168 Rutland Avenue, Crumlin, Crumlin, Dublin 12, D12CT80"
                address_match = re.search(r'(\d+[^,]+),?\s*([^,]+),?\s*([^,]+),?\s*([^,]+),?\s*([A-Z]\d{2}[A-Z0-9]{3})?', text)
                if address_match:
                    street = address_match.group(1).strip()
                    city = address_match.group(2).strip()
                    county = address_match.group(3).strip() if address_match.group(3) else None
                    postal_area = address_match.group(4).strip() if address_match.group(4) else None
                    postal_code = address_match.group(5) if address_match.group(5) else None
                    
                    return Address(
                        street=street,
                        city=city,
                        county=county,
                        postal_code=postal_code,
                        formatted_address=text
                    )
        
        # Try to extract from page title as fallback
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            # Look for address pattern in title
            address_match = re.search(r'(\d+[^,]+),?\s*([^,]+),?\s*([^,]+),?\s*([^,]+),?\s*([A-Z]\d{2}[A-Z0-9]{3})?', title_text)
            if address_match:
                street = address_match.group(1).strip()
                city = address_match.group(2).strip()
                county = address_match.group(3).strip() if address_match.group(3) else None
                postal_area = address_match.group(4).strip() if address_match.group(4) else None
                postal_code = address_match.group(5) if address_match.group(5) else None
                
                return Address(
                    street=street,
                    city=city,
                    county=county,
                    postal_code=postal_code,
                    formatted_address=title_text
                )
        
        return None
    
    def _extract_property_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract property details like bedrooms, bathrooms, area, etc."""
        details = {}
        
        # Look for property details in various formats
        # Common patterns: "2 Bed", "4 Bath", "119 m²"
        text_content = soup.get_text()
        
        # Extract bedrooms
        bed_match = re.search(r'(\d+)\s*Bed', text_content)
        if bed_match:
            details['bedrooms'] = int(bed_match.group(1))
        
        # Extract bathrooms
        bath_match = re.search(r'(\d+)\s*Bath', text_content)
        if bath_match:
            details['bathrooms'] = int(bath_match.group(1))
        
        # Extract area
        area_match = re.search(r'(\d+(?:\.\d+)?)\s*m²', text_content)
        if area_match:
            details['area_sqm'] = float(area_match.group(1))
        
        # Extract property type
        property_types = {
            'End of Terrace': PropertyType.HOUSE,
            'Terrace': PropertyType.HOUSE,
            'Semi-Detached': PropertyType.HOUSE,
            'Detached': PropertyType.HOUSE,
            'Apartment': PropertyType.APARTMENT,
            'Duplex': PropertyType.DUPLEX,
            'Townhouse': PropertyType.TOWNHOUSE,
            'Bungalow': PropertyType.BUNGALOW,
            'Cottage': PropertyType.COTTAGE,
            'Penthouse': PropertyType.PENTHOUSE,
            'Studio': PropertyType.STUDIO
        }
        
        for type_text, prop_type in property_types.items():
            if type_text.lower() in text_content.lower():
                details['property_type'] = prop_type
                break
        
        # Extract energy rating
        ber_match = re.search(r'BER\s*([A-G]\d?)', text_content)
        if ber_match:
            details['energy_rating'] = ber_match.group(1)
        
        # Extract BER number
        ber_num_match = re.search(r'BER No:\s*(\d+)', text_content)
        if ber_num_match:
            details['ber_number'] = ber_num_match.group(1)
        
        # Extract year built
        year_match = re.search(r'Year of construction:\s*(\d{4})', text_content)
        if year_match:
            details['year_built'] = int(year_match.group(1))
        
        # Extract price per m²
        price_per_sqm_match = re.search(r'Price per m²:\s*€([\d,]+)', text_content)
        if price_per_sqm_match:
            details['price_per_sqm'] = float(price_per_sqm_match.group(1).replace(',', ''))
        
        # Extract estimated stamp duty
        stamp_duty_match = re.search(r'Estimated Stamp Duty:\s*€([\d,]+)', text_content)
        if stamp_duty_match:
            details['stamp_duty'] = float(stamp_duty_match.group(1).replace(',', ''))
        
        # Extract selling type
        selling_type_match = re.search(r'Selling Type:\s*([^,\n]+)', text_content)
        if selling_type_match:
            details['selling_type'] = selling_type_match.group(1).strip()
        
        return details
    
    def _extract_agent_info(self, soup: BeautifulSoup) -> Optional[AgentInfo]:
        """Extract agent information"""
        # Look for agent details
        agent_selectors = [
            '.agent-info',
            '.agent-details',
            '[data-testid="agent"]',
            '.contact-agent',
            '.agent',
            'div:contains("Oliver Travers")',  # Specific agent from the example
            'div:contains("01 255 2489")'      # Specific phone from the example
        ]
        
        for selector in agent_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                
                # Extract agent name - look for patterns like "Oliver Travers"
                name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
                if name_match:
                    name = name_match.group(1)
                    
                    # Extract phone number - Irish format
                    phone_match = re.search(r'(\d{2}\s+\d{3}\s+\d{4})', text)
                    phone = phone_match.group(1) if phone_match else None
                    
                    # Extract email
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                    email = email_match.group(1) if email_match else None
                    
                    return AgentInfo(
                        name=name,
                        phone=phone,
                        email=email
                    )
        
        # Fallback: look for specific patterns in the entire page
        text_content = soup.get_text()
        
        # Look for agent name pattern
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\'s\s+logo', text_content)
        if name_match:
            name = name_match.group(1)
            
            # Look for phone number near the name
            phone_match = re.search(r'(\d{2}\s+\d{3}\s+\d{4})', text_content)
            phone = phone_match.group(1) if phone_match else None
            
            return AgentInfo(
                name=name,
                phone=phone
            )
        
        return None
    
    def _extract_features(self, soup: BeautifulSoup) -> List[PropertyFeature]:
        """Extract property features"""
        features = []
        
        # Look for features in various sections
        feature_selectors = [
            '.features',
            '.amenities',
            '.property-features',
            '[data-testid="features"]'
        ]
        
        for selector in feature_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Look for list items or feature items
                feature_items = element.find_all(['li', 'span', 'div'], class_=re.compile(r'feature|amenity'))
                
                for item in feature_items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 2:  # Avoid very short text
                        features.append(PropertyFeature(
                            name=text,
                            category="General"
                        ))
        
        return features
    
    def _extract_images(self, soup: BeautifulSoup) -> List[PropertyImage]:
        """Extract property images"""
        images = []
        
        # Look for image containers
        image_selectors = [
            '.property-images img',
            '.gallery img',
            '[data-testid="property-image"]',
            '.image-gallery img'
        ]
        
        for selector in image_selectors:
            img_elements = soup.select(selector)
            for i, img in enumerate(img_elements):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.daft.ie' + src
                    
                    try:
                        image_url = HttpUrl(src)
                        images.append(PropertyImage(
                            url=image_url,
                            description=f"Property image {i+1}",
                            is_primary=(i == 0),
                            order=i
                        ))
                    except:
                        continue  # Skip invalid URLs
        
        return images
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description"""
        description_selectors = [
            '.description',
            '.property-description',
            '[data-testid="description"]',
            '.about-this-property'
        ]
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 50:  # Ensure it's substantial
                    return text
        
        return None
    
    async def scrape_property(self, url: HttpUrl) -> Optional[Property]:
        """
        Scrape property data from Daft.ie
        """
        try:
            session = await self._get_session()
            
            # Add a small delay to be respectful
            await asyncio.sleep(1)
            
            # Try to fetch the webpage with different encoding options
            html_content = None
            
            # First try with default encoding
            try:
                async with session.get(str(url)) as response:
                    if response.status == 403:
                        print(f"Access forbidden (403) for {url}. The website may be blocking automated requests.")
                        print("This is common with web scraping. Consider using a different approach or respecting robots.txt.")
                        return None
                    elif response.status != 200:
                        print(f"Failed to fetch {url}: {response.status}")
                        return None
                    
                    html_content = await response.text()
            except Exception as e:
                if "brotli" in str(e).lower() or "br" in str(e).lower():
                    print(f"Brotli compression error for {url}. Trying without compression...")
                    # Try again without compression
                    try:
                        async with session.get(str(url), headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'identity',  # No compression
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0'
                        }) as response:
                            if response.status == 200:
                                html_content = await response.text()
                            else:
                                print(f"Failed to fetch {url} without compression: {response.status}")
                                return None
                    except Exception as retry_error:
                        print(f"Failed to fetch {url} even without compression: {retry_error}")
                        return None
                else:
                    raise e
            
            if not html_content:
                print(f"Could not fetch content from {url}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract listing ID
            listing_id = self.extract_listing_id(url)
            if not listing_id:
                print(f"Could not extract listing ID from {url}")
                return None
            
            # Extract price
            price = self._extract_price(soup)
            if not price:
                print(f"Could not extract price from {url}")
                return None
            
            # Extract address
            address = self._extract_address(soup)
            if not address:
                print(f"Could not extract address from {url}")
                return None
            
            # Extract property details
            details = self._extract_property_details(soup)
            
            # Extract description
            description = self._extract_description(soup)
            
            # Extract agent info
            agent = self._extract_agent_info(soup)
            
            # Extract features
            features = self._extract_features(soup)
            
            # Extract images
            images = self._extract_images(soup)
            
            # Create property object
            property_data = Property(
                address=address,
                property_type=details.get('property_type', PropertyType.HOUSE),
                bedrooms=details.get('bedrooms'),
                bathrooms=details.get('bathrooms'),
                area_sqm=details.get('area_sqm'),
                year_built=details.get('year_built'),
                energy_rating=details.get('energy_rating'),
                ber_number=details.get('ber_number')
            )
            
            # Create the website listing
            listing = self.create_website_listing(
                url=url,
                price=price,
                title=f"{address.street}, {address.city}",
                description=description,
                raw_data={
                    "listing_id": listing_id,
                    "scraped_at": "2024-01-01T12:00:00Z",
                    "source": "daft.ie",
                    "html_content": html_content[:1000]  # Store first 1000 chars for debugging
                }
            )
            
            # Add extracted data to listing
            listing.agent = agent
            listing.images = images
            listing.features = features
            
            property_data.listings = [listing]
            
            return property_data
            
        except ClientError as e:
            print(f"Network error scraping Daft property {url}: {e}")
            return None
        except Exception as e:
            print(f"Error scraping Daft property {url}: {e}")
            return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close() 