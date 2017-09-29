from ingest import load_database, read_addresses
import pandas
import re
import tldextract


class MainResult:
    """The main GoogleResult associated to somebody"""

    def __init__(self, siteName):
        self.certified = False
        self.candidates = []
        self.certifiedResult = None
        self.certifiedLink = None
        self.siteName = siteName

    def print(self):
        print('  {0}? {1} ({2} candidates): {3} ->> {4}'.format(
            self.siteName,
            self.certified,
            len(self.candidates),
            self.certifiedResult.name,
            self.certifiedLink))
        try:
            print('     {0}'.format(self.certifiedResult.description[:30]))
        except AttributeError:
            pass


class LinkedInResult(MainResult):
    def __init__(self):
        super().__init__('LinkedIn')


class ResearchGateResult(MainResult):
    def __init__(self):
        super().__init__('ResearchGate')


class PersonalPageResult(MainResult):
    def __init__(self):
        super().__init__('personal page')


def sanitize_string(s):
    """Return the string, or a blank if invalid"""
    try:
        return s + ''
    except TypeError:
        return ''


# -------------------
# person-class functions

def get_name(email, single_string=False):
    """Get dictionary of personal details from email"""
    df = read_addresses()
    row = df[df['EmailAddress'].values == email]

    first = sanitize_string(row['FirstName'].values[0])
    last = sanitize_string(row['LastName'].values[0])
    company = sanitize_string(row['CompanyName'].values[0])
    country = sanitize_string(row['Country'].values[0])

    if single_string:
        return first + ' ' + last
    else:
        return {'first': first, 'last': last, 'country': country, 'company': company}


# result-class functions
def is_LinkedinURL(result):
    """A LinkedIn GoogleResult"""
    return 'linkedin.' in result.link


def is_nameInTitle(result, name):
    """Somebody's name is mentioned in the result title"""
    return [name['first'].lower() in result.name.lower() and
            name['last'].lower() in result.name.lower()]


# has-class functions
def has_Linkedin(email, results):
    """Get somebody's LinkedIn details"""
    candidates = []
    certified = False
    certifiedResult = None
    certifiedLink = None

    for r in results:
        if not is_LinkedinURL(r):
            continue

        nameDict = get_name(email)
        valid = is_nameInTitle(r, nameDict)
        valid = valid and r'/pub/' not in r.link
        valid = valid and nameDict['company'].lower() in r.description.lower()

        if valid:
            certified = True
            certifiedResult = r
            certifiedLink = r.link
            candidates.append(r)

    result = LinkedInResult()
    result.certified = certified
    result.candidates = candidates
    result.certifiedResult = certifiedResult
    result.certifiedLink = certifiedLink
    return result


def has_ResearchGate(email, results):
    """Get somebody's ResearchGate details"""
    candidates = []
    certified = False
    certifiedResult = None
    certifiedLink = None

    for r in results:
        if 'researchgate.net' not in r.link:
            continue

        nameDict = get_name(email)
        valid = is_nameInTitle(r, nameDict)
        valid = valid and r'/profile/' in r.link and nameDict['last'] in r.link

        if valid:
            certified = True
            certifiedResult = r
            certifiedLink = r.link
            candidates.append(r)

    result = ResearchGateResult()
    result.certified = certified
    result.candidates = candidates
    result.certifiedResult = certifiedResult
    result.certifiedLink = certifiedLink
    return result


def has_personal_page(email, results):
    """Get somebody's personal page details"""
    candidates = []
    certified = False
    certifiedResult = None
    certifiedLink = None

    for r in results:
        # Skip documents
        linkExt = r.link[-4:]
        if linkExt in ['.pdf', '.doc', '.csv', '.xls', '.doc']:
            continue

        # Forbidden domains
        if is_LinkedinURL(r):
            continue
        domains = ['facebook', 'twitter', 'holaconnect', 'crunchbase', 'namenfinden']
        if any(d in r.link for d in domains):
            continue

        # Parse domains from email and link
        emailDomain = email.split('@')[-1]
        linkComponents = tldextract.extract(r.link)

        # Personal page must contain his name/surname somewhere in the title
        nameDict = get_name(email)

        valid = (nameDict['first'].lower() in r.name.lower() or
                 nameDict['last'].lower() in r.name.lower())

        # Company must be contained in link description
        valid = valid and nameDict['company'].lower() in r.description.lower()

        # Must be a contact page
        v1 = re.match('[ck]ontact', r.name.lower())
        # Email should have the same domain as the link
        v2 = (emailDomain == (linkComponents.domain + '.' + linkComponents.suffix))
        # or last name contained in link
        v3 = nameDict['last'].lower() in r.link

        valid = valid and (v1 or v2 or v3)

        if valid:
            certified = True
            certifiedResult = r
            certifiedLink = r.link
            candidates.append(r)

    result = PersonalPageResult()
    result.certified = certified
    result.candidates = candidates
    result.certifiedResult = certifiedResult
    result.certifiedLink = certifiedLink
    return result


def print_Person(email, results, linkedin=False, personal=False, researchgate=False):
    """Print someone's details"""

    nn = get_name(email)

    ll = has_Linkedin(email, results)
    pp = has_personal_page(email, results)
    rg = has_ResearchGate(email, results)

    print("*** {0} {1} @ {2} - {3} ***".format(nn['first'], nn['last'], nn['company'], email))

    if linkedin and ll.certified:
        ll.print()
    if personal and pp.certified:
        pp.print()
    if researchgate and rg.certified:
        rg.print()


def print_Results(results):
    """Pretty print a list of GoogleResults"""
    for r in results:
        print('{0}: {1}'.format(r.index, r.link))
        print('   {0}'.format(r.name))
        # print('   {0}'.format(r.description))


if __name__ == '__main__':

    db = load_database('database.pickle')
    emails = list(db.keys())
    emailsValid = [e for e in emails if db[e] is not None]

    # Show and store summary stats
    summaries = []
    try:
        for e in emailsValid:
            results = db[e]

            print_Person(e, results, researchgate=True, personal=True)
            name = get_name(e)

            # Linkedin
            ll = has_Linkedin(e, results)
            # lr = ll.certifiedResult

            # Personal pages
            pp = has_personal_page(e, results)
            # lp = pp.certifiedResult

            # ResearchGate
            rg = has_ResearchGate(e, results)
            # lr = rg.certifiedResult

            # Summarize results to output file
            summary = {}
            summary['email'] = e
            summary['firstName'] = name['first']
            summary['lastName'] = name['last']
            summary['company'] = name['company']

            summary['linkedinCertified'] = ll.certified
            summary['linkedinLink'] = ll.certifiedLink

            summary['personalCertified'] = pp.certified
            summary['personalLink'] = pp.certifiedLink

            summary['researchgateCertified'] = rg.certified
            summary['researchgateLink'] = rg.certifiedLink
            summaries.append(summary)

        # Export dataframe
        print('Exporting dataframe...')
        df_summaries = pandas.DataFrame(summaries)
        df_summaries.to_csv('results.csv', sep=';', index=False)
        print('Done.')

    except KeyboardInterrupt:
        print('')
        print('*** Aborting (interrupt) ***')
