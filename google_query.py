import google


def do_google_query(query_mail):
    num_page = 1
    search_results = google.standard_search.search(query_mail, num_page)
    return(search_results)
