"""
Read the set of Google results stored in the database.

Try to classify each Google result as LinkedIn/ResearchGate/personal page.

Export results.csv containing parsed and certified data.
"""

from ingest import load_database, get_name
import pandas
import re
import tldextract


class PersonInformationResult:
    """Class which extracts and represents personal information from a list of GoogleResults.

    This class is derived in order to implement extraction from ResearchGate / LinkedIn / personal page results.

    A GoogleResult is certified if we can extract information from it.
    If self.certified is False, the result is not verified and should NOT be exported.

    There is only one certified result per person (the first one).
    
    self.candidates contains other candidate GoogleResults which satisfy criteria.
    """

    def __init__(self, email, siteName, results=None):
        # Email associated to the Google search
        self.email = email
        # Target website to locate information
        self.siteName = siteName

        # True if a matching GoogleResult has been found
        self.certified = False
        # Best matching GoogleResult
        self.certifiedResult = None
        self.certifiedLink = None
        # Other matching GoogleResults
        self.candidates = []

        if results is not None:
            self.populateFromGoogleResults(results)


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

    def populateFromGoogleResults(self, results):
        """Parse a list of GoogleResults and find the most relevant."""
        self.candidates = []
        self.certified = False
        self.certifiedResult = None
        self.certifiedLink = None

        for r in results:
            # Check if we can extract information from the GoogleResult 
            valid = self.validate_result(r)

            if valid:
                # Multiple matches:
                #   certify only the first result
                #   append the others to candidates
                if not self.certified:
                    self.certified = True
                    self.certifiedResult = r
                    self.certifiedLink = r.link
                else:
                    self.candidates.append(r)

    def validate_result(self, result):
        """Return True if we can extract information from a GoogleResult.
        Must be overwritten by derived classes."""
        raise NotImplementedError()

# -------------------
# Derived classes for each GoogleResult.
#
# They define how to extract information from a GoogleResult according to website types.    


class LinkedInResult(PersonInformationResult):
    """Get somebody's LinkedIn details"""

    def __init__(self, email, results):
        super().__init__(email=email, siteName='LinkedIn', results=results)

    def validate_result(self, result):
        if not ('linkedin.' in result.link):
            return False

        nameDict = get_name(self.email)
        valid = is_nameInTitle(result, nameDict)
        valid = valid and r'/pub/' not in result.link
        valid = valid and nameDict['company'].lower() in result.description.lower()
        return valid


class ResearchGateResult(PersonInformationResult):
    """Get somebody's ResearchGate details"""

    def __init__(self, email, results):
        super().__init__(email=email, siteName='ResearchGate', results=results)

    def validate_result(self, result):
        if 'researchgate.net' not in result.link:
            return False

        nameDict = get_name(self.email)
        valid = is_nameInTitle(result, nameDict)
        valid = valid and r'/profile/' in result.link and nameDict['last'] in result.link
        return valid


class PersonalPageResult(PersonInformationResult):
    """Get somebody's personal page (experimental)"""

    def __init__(self, email, results):
        super().__init__(email=email, siteName='personal page', results=results)

    def validate_result(self, result):
        # Skip documents
        linkExt = result.link[-4:]
        if linkExt in ['.pdf', '.doc', '.csv', '.xls', '.doc']:
            return False

        # Forbidden domains
        domains = ['facebook', 'twitter', 'holaconnect', 'crunchbase', 'namenfinden']
        if any(d in result.link for d in domains):
            return False

        # Parse domains from email and link
        emailDomain = self.email.split('@')[-1]
        linkComponents = tldextract.extract(result.link)

        # Personal page must contain his name/surname somewhere in the title
        nameDict = get_name(self.email)

        valid = (nameDict['first'].lower() in result.name.lower() or
                 nameDict['last'].lower() in result.name.lower())

        # Company must be contained in link description
        valid = valid and nameDict['company'].lower() in result.description.lower()

        # Must be a contact page
        v1 = re.match('[ck]ontact', result.name.lower())
        # Email should have the same domain as the link
        v2 = (emailDomain == (linkComponents.domain + '.' + linkComponents.suffix))
        # or last name contained in link
        v3 = nameDict['last'].lower() in result.link

        valid = valid and (v1 or v2 or v3)
        return valid


# -------------------
# GoogleResult-class functions
#
# These functions associate objects to each GoogleResult
# is_* return TRUE if a given GoogleResult satisfies a given criterium


def is_nameInTitle(result, name):
    """Somebody's name is mentioned in the webpage title"""
    return [name['first'].lower() in result.name.lower() and
            name['last'].lower() in result.name.lower()]

# -------------------
# Printing functions


def print_Person(email, results, linkedin=False, personal=False, researchgate=False):
    """Print someone's details"""

    nn = get_name(email)

    ll = LinkedInResult(email, results)
    pp = PersonalPageResult(email, results)
    rg = ResearchGateResult(email, results)

    print("*** {0} {1} @ {2} - {3} ***".format(
        nn['first'], nn['last'], nn['company'], email))

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


def sanitize_string(s):
    """Return the string, or a blank if invalid"""
    try:
        return s + ''
    except TypeError:
        return ''


if __name__ == '__main__':
    """
    Load the database with stored Google results.
    Parse each result and instantiate corresponding objects.
    Export at the end.
    """

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

            # Start classifying obtained GoogleResults

            # Linkedin
            ll = LinkedInResult(e, results)
            # lr = ll.certifiedResult

            # Personal pages
            pp = PersonalPageResult(e, results)
            # lp = pp.certifiedResult

            # ResearchGate
            rg = ResearchGateResult(e, results)
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
