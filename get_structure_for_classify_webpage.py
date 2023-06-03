import sys
import urllib3
from bs4 import BeautifulSoup, Tag
from pprint import pprint
import re
from urllib.parse import urlparse
import collections
sys.path.append('/home/tom/projects/tools')
from common import get_methods
import requests
from requests.exceptions import HTTPError


def get_web_page(url):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
        }
    print(f"getting page: {url}")
    http = urllib3.PoolManager(headers=headers, timeout=5)
    try:
        response = http.request('GET', url)

        if response.status != 200:
            raise Exception(response.status)
        return response

    except requests.exceptions.Timeout as err:
        raise Exception(err)
    except requests.exceptions.TooManyRedirects as err:
        raise Exception(err)
    except requests.exceptions.RequestException as err:
        raise Exception(err)
    except requests.exceptions.ConnectionError as err:
        raise Exception(err)
       
def remove_empty_tags(soup):
    for tag in soup.find_all(True):
        if isinstance(tag, Tag) and not tag.contents and not tag.string:
            tag.extract()

def remove_attributes(tag):
    for attribute in list(tag.attrs):
        del tag[attribute]
    return tag

def one_line(tag):
    string = ''.join(tag.stripped_strings)
    return re.sub(r"\n", " ", string)

def replace_newline_except_last(string):
    result = re.sub(r"\n", " ", string)
    return result

def get_header_outline(html):
    soup = BeautifulSoup(html, 'html.parser')
    remove_empty_tags(soup)
    h_tags = soup.find_all(['title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    content = []
    title_tag_done = 0
    for tag in h_tags:
        clean_tag = remove_attributes(tag)
        if clean_tag.name == "title" and title_tag_done == 1:
            continue
        tag_content = one_line(clean_tag)

#        content.append(f"<{clean_tag.name}>{tag_content}</{clean_tag.name}>")
        if clean_tag.name == "title":
            title_tag_done = 1
       

        content.append(f"{clean_tag.name}:{tag_content}")
    return content

def count_words_in_paragraphs(html, sample_word_count):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <p> tags
    paragraphs = soup.find_all('p')

    word_count = 0
    sample_words = ""

    for p in paragraphs:
        # Get text inside <p> tag
        text = p.get_text()

        # Split text into words based on white spaces and count the words
        words = text.split()
        words[-1] += " "

        # Update the word count
        word_count += len(words)

        if sample_word_count > 0:
            if sample_word_count < word_count:
                sample_words += " ".join(words)
                sample_word_count -= word_count
            else:
                sample_words += " ".join(words[0:sample_word_count])
                sample_word_count -= word_count


    sample_words = sample_words.strip()
    p_count = len(paragraphs)

    return { "word_count": word_count, "sample_words": sample_words, "p_count": p_count }

def list_info(html):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <ol> and <ul> tags
    ordered_lists = soup.find_all('ol')
    unordered_lists = soup.find_all('ul')

    # Count the number of each type of list
    ol_count = len(ordered_lists)
    ul_count = len(unordered_lists)

    # Return the counts as a dictionary
    lists = {'ol_count': ol_count, 'ul_count': ul_count}
    return lists

def link_info(html, url):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Find all <a> tags
    a_tags = soup.find_all('a')

    internal_counts = collections.defaultdict(int)
    external_counts = collections.defaultdict(int)
    general_counts = collections.defaultdict(int)
    internal_links = []
    external_links = []
    link_info = {}

    # Parse the provided URL to get its domain
    parsed_provided_url = urlparse(url)
    provided_domain = parsed_provided_url.netloc

    for a in a_tags:
        # Get the href attribute
        href = a.get('href')
        # If href is None, continue to the next iteration
        if not href:
            continue

        # Parse the URL
        parsed_url = urlparse(href)

        if href.startswith("#"):
            internal_counts["bookmark_count"] += 1
            continue


        uri_scheme_match = re.match(r"[^:]+:", href)
        if uri_scheme_match:
            uri_scheme = uri_scheme_match.group().rstrip(":")
            if (uri_scheme != "https") and (uri_scheme != "http"):
                continue
        
        # Check if the href starts with the provided domain, or if the domain of the parsed URL matches the provided domain
        if href.startswith("https://" + provided_domain) or href.startswith("http://" + provided_domain) or (href.startswith(provided_domain) and not parsed_url.netloc):
            internal_counts["internal_link_count"] += 1
            internal_links.append(href)
        else:
            external_counts["external_link_count"] += 1
            external_links.append(href)

    link_info = { 
        "internal": internal_counts, 
        "external": external_counts, 
        "general": general_counts, 
        "internal_links": internal_links, 
        "external_links": external_links 
        }

    return link_info


def get_outline( url, num_sample_words ):
    response = get_web_page(url)
    
    html_data = response.data
    url = response.geturl() # Get the proper full url

    header_outline = get_header_outline(html=html_data)
    p_counts = count_words_in_paragraphs(html=html_data,sample_word_count=num_sample_words)
    links = link_info(html=html_data, url=url)
    lists = list_info(html=html_data)

    outline = { "header_outline": header_outline }
    outline.update(links)
    outline.update(p_counts)
    outline.update(lists)
    outline.update({"url": url})
    return outline


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    result = {}

    try:
        result = get_outline(url=url, num_sample_words=25)
    except Exception as err:
        print(f"Error getting outline: {err}")
        #traceback.print_stack()
    

    pprint(result)
