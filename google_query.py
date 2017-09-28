from google import google


def do_query(query_mail):
    num_page = 1
    search_results = google.search(query_mail, num_page)
    return(search_results)
