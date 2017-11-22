import google


def do_google_query(query):
    """Perform a Google search using a query string. Return GoogleResults in the first page."""
    num_page = 1
    search_results = google.standard_search.search(query, num_page)
    return(search_results)
