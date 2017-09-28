from ingest import load_database, read_addresses
import pandas as pd
import re
import tldextract


def sanitize_string(s):
    try:
        return s + ''
    except TypeError:
        return ''


# person-class functions
def get_name(email, singleName=False):
    df = read_addresses()
    row = df[df['EmailAddress'].values == email]

    first = sanitize_string(row['FirstName'].values[0])
    last = sanitize_string(row['LastName'].values[0])
    company = sanitize_string(row['CompanyName'].values[0])
    country = sanitize_string(row['Country'].values[0])
    if singleName:
        return first + ' ' + last
    else:
        return {'first': first, 'last': last, 'country': country, 'company': company}


# is-class functions
def is_LinkedinURL(result):
    return 'linkedin.' in result.link


def is_nameInTitle(result, name):
    return [name['first'].lower() in result.name.lower() and 
        name['last'].lower() in result.name.lower()]


# has-class functions
def has_Linkedin(email, results):
    candidates = []
    certified = False
    certifiedResult = None
    certifiedLink = None

    for r in results:
        if is_LinkedinURL(r):
            nameDict = get_name(email)
            valid = is_nameInTitle(r, nameDict)
            valid = valid and r'/pub/' not in r.link
            valid = valid and nameDict['company'].lower() in r.description.lower()

            if valid:
                certified = True
                certifiedResult = r
                certifiedLink = r.link

            candidates.append(r)

    return {
        'certified': certified,
        'candidates': candidates,
        'certifiedResult': certifiedResult,
        'certifiedLink': certifiedLink
    }


def has_researchgate(email, results):
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

    return {
        'certified': certified,
        'candidates': candidates,
        'certifiedResult': certifiedResult,
        'certifiedLink': certifiedLink
    }


def has_personal_page(email, results):
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
        if ('facebook' in r.link or
            'twitter' in r.link or
            'holaconnect' in r.link or
            'crunchbase' in r.link or
            'namenfinden' in r.link):
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

    return {
        'certified': certified,
        'candidates': candidates,
        'certifiedResult': certifiedResult,
        'certifiedLink': certifiedLink
    }


def print_Person(email, results, linkedin=False, personal=False, researchgate=False):

    nn = get_name(email)

    ll = has_Linkedin(email, results)
    pp = has_personal_page(email, results)
    rg = has_researchgate(email, results)

    print("*** {0} {1} @ {2} - {3} ***".format(nn['first'], nn['last'], nn['company'], email))

    if linkedin and ll['certified']:
        print('{0}: {1}'.format(email, get_name(email, singleName=True)))
        print('  LINKEDIN? {0} ({1} candidates): {2} ->> {3}'.format(
            ll['certified'],
            len(ll['candidates']),
            ll['certifiedResult'].name,
            ll['certifiedResult'].link))
        print('     {0}'.format(ll['certifiedResult'].description[:30]))

    if personal and pp['certified']:
        print('  PERSONAL? {0} ({1} candidates): {2} ->> {3}'.format(
            pp['certified'],
            len(pp['candidates']),
            pp['certifiedResult'].name,
            pp['certifiedResult'].link))
        print('     {0}'.format(pp['certifiedResult'].description[:30]))

    if researchgate and rg['certified']:
        print('  RESEARCHGATE? {0} ({1} candidates): {2} ->> {3}'.format(
            rg['certified'],
            len(rg['candidates']),
            rg['certifiedResult'].name,
            rg['certifiedResult'].link))
        print('     {0}'.format(rg['certifiedResult'].description[:30]))


def print_Results(results):
    for r in results:
        print('{0}: {1}'.format(r.index, r.link))
        print('   {0}'.format(r.name))
        # print('   {0}'.format(r.description))


if __name__ == '__main__':

    db = load_database('database.pickle')
    emails = list(db.keys())
    emailsValid = [e for e in emails if db[e] is not None]

    # Show summary stats
    summaries = []
    try:
        for e in emailsValid:
            results = db[e]

            print_Person(e, results, personal=True)
            nn = get_name(e)

            # Linkedin
            ll = has_Linkedin(e, results)
            if ll['certified']:
                lr = ll['certifiedResult']

            # Personal pages
            pp = has_personal_page(e, results)
            if pp['certified']:
                lp = pp['certifiedResult']

            # Researchgate
            rg = has_researchgate(e, results)
            if rg['certified']:
                lr = rg['certifiedResult']

            summary = {}
            summary['email'] = e
            summary['firstName'] = nn['first']
            summary['lastName'] = nn['last']
            summary['company'] = nn['company']

            summary['linkedinCertified'] = ll['certified']
            summary['linkedinLink'] = ll['certifiedLink']

            summary['personalCertified'] = pp['certified']
            summary['personalLink'] = pp['certifiedLink']

            summary['researchgateCertified'] = rg['certified']
            summary['researchgateLink'] = rg['certifiedLink']
            summaries.append(summary)

        # Export dataframe
        print('Exporting dataframe...')
        df_summaries = pd.DataFrame(summaries)
        df_summaries.to_csv('results.csv', sep=';', index=False)
        print('Done.')

    except KeyboardInterrupt:
        print('')
        print("*** Aborting (interrupt) ***")
