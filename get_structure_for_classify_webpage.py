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
from itertools import groupby
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import copy

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
        

    except requests.exceptions.Timeout as err:
        raise Exception(err)
    except requests.exceptions.TooManyRedirects as err:
        raise Exception(err)
    except requests.exceptions.RequestException as err:
        raise Exception(err)
    except requests.exceptions.ConnectionError as err:
        raise Exception(err)

    html_data = response.data
    url = response.geturl() # Get the proper full url

    return (html_data, url)

def get_web_page_with_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(15)


    try:
        driver.get(url)
    except Exception as err:
        raise Exception(err)

    html = driver.page_source
    url = driver.current_url

    return(html, url)



def _remove_empty_tags(soup):
    for tag in soup.find_all(True):
        if isinstance(tag, Tag) and not tag.contents and not tag.string:
            tag.extract()

def _remove_attributes(tag):
    for attribute in list(tag.attrs):
        del tag[attribute]
    return tag

def _one_line(tag):
    string = ''.join(tag.stripped_strings)
    return re.sub(r"\n", " ", string)

def _replace_newline_except_last(string):
    result = re.sub(r"\n", " ", string)
    return result

def get_header_outline(html):
    soup = BeautifulSoup(html, 'html.parser')
    _remove_empty_tags(soup)
    h_tags = soup.find_all(['title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    content = []
    title_tag_done = 0
    for tag in h_tags:
        clean_tag = _remove_attributes(tag)
        if clean_tag.name == "title" and title_tag_done == 1:
            continue
        tag_content = _one_line(clean_tag)

        if clean_tag.name == "title":
            title_tag_done = 1
       

        content.append(f"{clean_tag.name}:{tag_content}")
    return content

def count_words_in_paragraphs(html, sample_word_count):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')
    _remove_empty_tags(soup)
    # Find all <p> tags
    for i in range(1, 7):
        for p_tag in soup.find_all('p'):
            _replace_p_with_heading(p_tag, i)

    paragraphs = soup.find_all('p')

    word_count = 0
    sample_words = ""

    for p in paragraphs:
        # Get text inside <p> tag
        text = p.get_text()

        # Split text into words based on white spaces and count the words
        words = text.split()
        if len(words) > 0:
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
    _remove_empty_tags(soup)

    # Find all <ol> and <ul> tags
    ordered_lists = soup.find_all('ol')
    unordered_lists = soup.find_all('ul')
    li_elements = soup.find_all('li')

    # Count the number of each type of list
    ol_count = len(ordered_lists)
    ul_count = len(unordered_lists)
    li_count = len(li_elements)
    li_contents = []

    for li in li_elements:
        clean_tag = _remove_attributes(li)
        li_content = _one_line(clean_tag)

        if li_content != "":
            li_contents.append(li_content)

    # Return the counts as a dictionary
    lists = {'ol_count': ol_count, 'ul_count': ul_count, 'li_count': li_count, 'li_contents': li_contents}
    return lists

def link_info(html, url):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')
    _remove_empty_tags(soup)

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
        
        clean_tag = _remove_attributes(a)
        anchor = _one_line(clean_tag)

        # Check if the href starts with the provided domain, or if the domain of the parsed URL matches the provided domain
        if href.startswith("https://" + provided_domain) or href.startswith("http://" + provided_domain) or (href.startswith(provided_domain) and not parsed_url.netloc):
            internal_counts["internal_link_count"] += 1
            internal_links.append({"anchor": anchor, "link": href})
        else:
            external_counts["external_link_count"] += 1
            external_links.append({"anchor": anchor, "link": href})

    link_info = { 
        "internal": internal_counts, 
        "external": external_counts, 
        "general": general_counts, 
        "internal_links": internal_links, 
        "external_links": external_links 
        }

    return link_info

def _count_tags(soup):
    counts = collections.defaultdict(int)
    
    # Iterate over all tags in the soup object, regardless of depth
    for tag in soup.find_all(True):
        counts[tag.name] += 1

    return dict(counts)

def count_all_tags(html):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    for i in range(1, 7):
        for p_tag in soup.find_all('p'):
            _replace_p_with_heading(p_tag, i)

    # Count tags in the head and body separately
    head_counts = _count_tags(soup.head) if soup.head else {}
    body_counts = _count_tags(soup.body) if soup.body else {}

    # Merge the two dictionaries
    all_counts = collections.defaultdict(int, head_counts)
    for tag, count in body_counts.items():
        all_counts[tag] += count

    return dict(all_counts)


## We always have a root. In this case it's "body".
## This makes it easier to use recursive functions.
def html_body_shorthand(html, tags):
    # Parse HTML data
    soup = BeautifulSoup(html, 'html.parser')

    # Replace <p> tags with the appropriate heading tags
    for i in range(1, 7):
        for p_tag in soup.find_all('p'):
            _replace_p_with_heading(p_tag, i)

    #[ { "tag": "name", "child": [], "use": True/False } ]
    tag_tree = [ { "_tag": "body", "_child": [], "_use": False, "_level": 0 } ]

    current_node = tag_tree[-1]["_child"]
    current_level = 0

    shorthand_tags = soup.body.find_all(True, recursive=False)

    ## Without the base root we couldn't do this, we'd have an ugly level 0 with multiple tags instead of just 1
    for tag in shorthand_tags:
        #print(f"Tag: {tag.name}")
        _build_parse_tree(node=current_node, tag=tag, whitelist_tags=tags, level=current_level)


    template_string = _generate_outline_shorthand(tag_tree)

    print(template_string)

def _print_tree(tree, level):
    for node in tree:
        if node["_use"] is True:
            print(f"{':' * level}{node['_tag']}")  

            if len(node["_child"]) > 0:
                _print_tree(node["_child"], level+1)
        elif node["_use"] is False:
            if len(node["_child"]) > 0:
                _print_tree(node["_child"], level)

def _generate_outline_shorthand(tree):
    string = ""
    for node in tree:
        if node["_use"] is True:
            string += node['_tag'] + ","

            if len(node["_child"]) > 0:
                string_test = ""
                string_test += _generate_outline_shorthand(node["_child"])
                if string_test:
                    string = string.rstrip(",")
                    string += '('
                    string += string_test.rstrip(",")
                    string += '),'
        elif node["_use"] is False:
            if len(node["_child"]) > 0:
                string += _generate_outline_shorthand(node["_child"])

    string.rstrip(",")

    return string

def _clean_template_string(template_string):
    template_string = re.sub(r'\(+\)', r'', template_string)
    template_string = re.sub(r'\){2,}', r'', template_string)
    template_string = re.sub(r'\){2,}', r'', template_string)
    template_string = re.sub(r',{2,}', r'', template_string)

    
def _remove_empty_nodes(node, index: int):

    return

       

def __node_has_children(node):
    if (len(node["_children"]) > 0):
        return 1
    else:
        #print(f"Failed children test: {node['_name']}")
        return 0


## This just makes the above more readable. The logic is really tricky so more english helps.
def __node_is_empty(node):
    #print(f"NAME: {node['_name']}")
    if node["_name"] == "EMPTY":
        return 1
    else:
        return 0


def _traverse_parse_tree_build_string(node):
    string = ""
    for child_node in node["_children"]:
        string += child_node["_name"] + ","
        if len(child_node["_children"]) > 0:
            string = string.strip(",")
            string += "("
            string += _traverse_parse_tree_build_string(child_node)
            string += "),"

    return string.rstrip(",")



def _build_parse_tree(node, tag, whitelist_tags, level):
    level += 1
    if tag.name in whitelist_tags:
        node.append( { "_tag": tag.name, "_child": [], "_use": True, "_level": level } )
    else:
        node.append( { "_tag": tag.name, "_child": [], "_use": False, "_level": level } )
    if tag.children:
        for child_tag in tag.children:
            if child_tag.name is None:
                continue
            else:
                child_node = node[-1]["_child"]
                _build_parse_tree(node=child_node, tag=child_tag, whitelist_tags=whitelist_tags, level=level)


# Function to replace paragraph tags with heading tags
# This is for sites that use things like <p class="h2">
# This works because it modifies soup's own internal data through the tag.name method call.
def _replace_p_with_heading(tag, heading_level):
    p_class = tag.get('class')
    if p_class and any(h_class in p_class for h_class in [f'h{heading_level}', f'heading{heading_level}', f'header{heading_level}', f'header-{heading_level}', f'heading-{heading_level}']):
        tag.name = f'h{heading_level}'
        tag.attrs = {} 


def get_outline( url, num_sample_words ):
    (html_data, url) = get_web_page(url)

    #(html_data, url) = get_web_page_with_selenium(url)
    #url = "https://www.lumar.io/learn/seo/search-engines/how-do-search-engines-work/"
    #html_data_fh = open("tmp.txt", "r")
    #html_data = html_data_fh.read()
    print(url)

    header_outline = get_header_outline(html=html_data)
    p_counts = count_words_in_paragraphs(html=html_data,sample_word_count=num_sample_words)
    links = link_info(html=html_data, url=url)
    lists = list_info(html=html_data)
    all_counts = count_all_tags(html=html_data)

    html_tags_for_template = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "a", "iframe", "img", "a", "code", "blockquote", "cite", "q", "pre", "object"]
    template_string = html_body_shorthand(html=html_data, tags=html_tags_for_template)

    outline = { "header_outline": header_outline }
    outline.update(links)
    outline.update(p_counts)
    outline.update(lists)
    outline.update({"url": url})
    outline.update({"all_counts": all_counts})
    outline.update({"template_string": template_string})
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
        traceback.print_stack()
    

    pprint(result)
