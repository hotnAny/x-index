import os
import csv
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import time

DEBUG = False

VENUE_INFO_DIR = './data/hci_venues.csv'
PAPER_COUNT_DIR = './data/paper_count.csv'

CHI_DIR = './data/chi'
UIST_DIR = './data/uist'
CSCW_DIR = './data/cscw'

WIDTH_FIG = 1200
HEIGHT_FIG = 675
DIR_OUTPUT_IMAGES = '/Users/hotnany/Library/CloudStorage/GoogleDrive-xac@g.ucla.edu/My Drive/Research/2023_X-index/write-up/figures'


# one measurement only concerns citations in the first N year after a paper is published
FIRST_N = 5

def clean_text(text):
    text_new = text.lower()
    text_new = text_new.replace('and', '')
    text_new = text_new.replace('&', '')
    text_new = text_new.replace('-', ' ')
    text_new = text_new.replace('–', ' ')
    return text_new

if __name__ == "__main__":

    # import a list of HCI venues
    ls_venues = []
    with open(VENUE_INFO_DIR, newline='') as f_venues:
        rdr_venues = csv.reader(f_venues, delimiter=',')
        for row in rdr_venues:
            # row[0] is acronym and row[1] is the identifier (longer name) of each HCI venue
            if row[1] == 'Identifier':
                continue
            venue = row[1]
            ls_venues.append(venue)
    if DEBUG:
        print(ls_venues)

    # import paper counts of each venue/year
    paper_counts = {}
    with open(PAPER_COUNT_DIR, newline='') as f_paper_counts:
        rdr_paper_counts = csv.reader(f_paper_counts, delimiter=',')
        for row in rdr_paper_counts:
            if row[1] == 'venue_year':
                continue
            paper_counts[row[0]] = row[1]
    if DEBUG:
            print(paper_counts)

    results = {}
    # e.g., results['uist2014'] = {'year': 2010, ...}

    dirs = [CHI_DIR, UIST_DIR, CSCW_DIR]
    
    # for each conference, e.g., CHI
    for dir in dirs:
        filenames = os.listdir(dir)
        filenames.sort()

        # for each year's conference, e.g., CHI 2020
        for f in filenames:
            if f.endswith('.ris') == False:
                continue

            print(f)

            result = {}

            # all files are assumed to be named as <venue><year>-citations-<date>.ris
            venue_year = f[0: f.find('-')].upper()
            result['year'] = venue_year[-4:]

            # measurement 1: X-index---% of non-HCI forward citations
            cnt_total_citations = 0
            cnt_hci_citations = 0
            distr_by_venue_cnt_hci_citations = {}
            for venue in ls_venues:
                distr_by_venue_cnt_hci_citations[venue] = 0

            # measurement 2: X-index in the first N years after a paper was published
            cnt_total_citations_firstn = 0
            cnt_hci_citations_firstn = 0

            # measurement 3: X-index broken down by citing-year (when the citations happened) for each venue/year
            distr_by_cite_year_cnt_hci_citations = {}
            distr_by_cite_year_cnt_total_citations = {}

            cite_year = None

            # for each citation to this venue/year's papers
            with open(os.path.join(dir, f), 'r') as f_papers:
                for line in f_papers:
                    if line.startswith('PY'):
                        cite_year = line[-5:-1]
                    
                    if line.startswith('JF'): 
                        # JF appears after PY for each citation record

                        # measurement 1 related: count each year's total citations
                        cnt_total_citations += 1

                        # measurement 2 related: count if the citation falls within first-N years
                        is_firstn = False
                        if len(cite_year) > 0 and ('NA' not in cite_year):
                            if cite_year not in distr_by_cite_year_cnt_hci_citations:
                                distr_by_cite_year_cnt_hci_citations[cite_year] = 0
                            if cite_year not in distr_by_cite_year_cnt_total_citations:
                                distr_by_cite_year_cnt_total_citations[cite_year] = 0
                            if int(cite_year) - int(result['year']) <= FIRST_N:
                                cnt_total_citations_firstn += 1
                                is_firstn = True

                        # measurement 3 related: count total citations broken down by the citing year
                        if cite_year in distr_by_cite_year_cnt_total_citations:
                            distr_by_cite_year_cnt_total_citations[cite_year] += 1

                        not_hci = True
                        for venue in ls_venues:
                            if clean_text(venue) in clean_text(line):
                                not_hci = False

                                # measurement 1 related: count each year's HCI citations
                                distr_by_venue_cnt_hci_citations[venue] += 1
                                cnt_hci_citations += 1
                                
                                # measurement 2 related: count each first n year's HCI citations
                                if is_firstn:
                                   cnt_hci_citations_firstn += 1

                                # measurement 3 related: count HCI citations broken down by the citing year
                                if cite_year in distr_by_cite_year_cnt_hci_citations:
                                    distr_by_cite_year_cnt_hci_citations[cite_year] += 1

                                break # each citation can only be from one venue
                                
                        if DEBUG and not_hci is True:
                            if int(round(time.time() * 1000)) % 1000 == 1:
                                print(line)

                        # after the JF line, cite_year should be reset as the entry will be ended
                        cite_year = ''
            
            result['non-hci-citations'] = cnt_total_citations - cnt_hci_citations
            result['x-index'] = 1 - cnt_hci_citations/cnt_total_citations
            result['x-index-firstn'] = 1 - cnt_hci_citations_firstn / cnt_total_citations_firstn
            result['x-index-distr-by-year'] = {}
            distr_by_cite_year_cnt_non_hci_citations = {}
            for cite_year in distr_by_cite_year_cnt_hci_citations:
                result['x-index-distr-by-year'][cite_year] = 1 - distr_by_cite_year_cnt_hci_citations[cite_year] / distr_by_cite_year_cnt_total_citations[cite_year]
                distr_by_cite_year_cnt_non_hci_citations[cite_year] = distr_by_cite_year_cnt_total_citations[cite_year] - distr_by_cite_year_cnt_hci_citations[cite_year]
            result['hci-citations-distr-by-cite-year'] = distr_by_cite_year_cnt_hci_citations
            result['non-hci-citations-distr-by-cite-year'] = distr_by_cite_year_cnt_non_hci_citations

            if DEBUG:
                print('total # of citations', cnt_total_citations)
                print('hci citations', cnt_hci_citations)
                print('hci citations', "within the first", FIRST_N, 'years', cnt_hci_citations_firstn)
                print('x-index', str(1 - cnt_hci_citations/cnt_total_citations))
                print('x-index-firstn', str(1 - cnt_hci_citations_firstn/cnt_total_citations_firstn))
                print(distr_by_cite_year_cnt_hci_citations)
                print(distr_by_cite_year_cnt_non_hci_citations)
                print(distr_by_cite_year_cnt_total_citations)

                print()

            results[venue_year] = result

    # print(results)

    # --------------------------------------------------------------------------------
    # 
    # plot measurement 1: x-index of each HCI venue over the years
    # 
    def plot_measurement_1():
        d = {}
        years = []
        venues = []
        start_year = 2010
        num_years = 11
        for dyear in range(0, num_years):
            year = start_year + dyear
            years.append(year)
            for venue_year in results:
                # the key in venue_year is <venue><4-digit-year>
                if str(year) != venue_year[-4:]:
                    continue

                venue = venue_year[:-4]
                if venue not in venues:
                    venues.append(venue)
                if venue not in d:
                    d[venue] = [float('NaN')] * num_years

                d[venue][dyear] = results[venue_year]['x-index']
        d['year'] = years

        df = pd.DataFrame(data=d)
        fig = px.line(df, x='year', y=venues, title="X-index")
        fig.update_layout(yaxis=dict(range=[0, 1]))
        if DEBUG:
            fig.show()
        pio.write_image(fig, os.path.join(DIR_OUTPUT_IMAGES,'fig1.png'), width=WIDTH_FIG, height=HEIGHT_FIG)

    # 
    # plot measurement 2: x-index of each HCI venue over the years, only including citations in the first n-years after (i.e., not including) that venue/year
    #  e.g., for uist2013, we count citations from 2014-2018 if n == 5
    # 
    def plot_measurement_2():
        d = {}
        years = []
        venues = []
        start_year = 2010
        num_years = 11 - FIRST_N
        for dyear in range(0, num_years):
            year = start_year + dyear
            years.append(year)
            for venue_year in results:
                if str(year) != venue_year[-4:]:
                    continue

                venue = venue_year[:-4]
                if venue not in venues:
                    venues.append(venue)
                if venue not in d:
                    d[venue] = [float('NaN')] * num_years
                
                d[venue][dyear] = results[venue_year]['x-index-firstn']
        d['year'] = years

        df = pd.DataFrame(data=d)
        fig = px.line(df, x='year', y=venues, title="X-index in the first " + str(FIRST_N) + " years after each conference" )
        fig.update_layout(yaxis=dict(range=[0, 1]))
        if DEBUG:
            fig.show()
        pio.write_image(fig, os.path.join(DIR_OUTPUT_IMAGES,'fig2.png'), width=WIDTH_FIG, height=HEIGHT_FIG)


    # 
    # plot measurement 3: x-index of each venue/year over the subsequent years (including that venue/year)
    # 
    def plot_measurement_3():
        years = []
        venues = ['CHI', 'UIST', 'CSCW']
        
        # here the year is NOT when a paper was published but when it was cited
        start_year = 2010
        num_years = 13 # until 2022

        for dyear in range(0, num_years):
            year = start_year + dyear
            years.append(year)

        for venue in venues:
            d = {}
            d['year'] = years
            venue_years = []
            
            for venue_year in results:
                if venue not in venue_year:
                    continue

                venue_years.append(venue_year)
                d[venue_year] = [float('NaN')] * num_years
                this_year = int(venue_year[-4:])
                for dyear in range(0, num_years):
                    cite_year = start_year + dyear
                    if cite_year < this_year:
                        continue
                    if str(cite_year) in results[venue_year]['x-index-distr-by-year']:
                        d[venue_year][dyear] = results[venue_year]['x-index-distr-by-year'][str(cite_year)]

            df = pd.DataFrame(data=d)
            fig = px.line(df, x='year', y=venue_years, title=venue + " X-index by year")
            fig.update_layout(yaxis=dict(range=[0, 1]))
            if DEBUG:
                fig.show()
            pio.write_image(fig, os.path.join(DIR_OUTPUT_IMAGES,'fig3_' + venue.upper() + '.png'), width=WIDTH_FIG, height=HEIGHT_FIG)

    # 
    # plot measurement 4: each year’s x-index based on citations of all HCI papers in the past n years
    # e.g., for 2015, we only consider that year's citations of HCI papers published in 2010-2015;
    # for n=5, we start counting from 2015 (2010+n) so that each year we consider its citations of the past 5 year's HCI papers
    # if we don't impose the constraint of n, some years don't have citations data of earlier paper (e.g., 2010's citations have no info of any cited 2009 papers because our forward citations start from 2010)
    def plot_measurement_4():
        cite_years = []
        venues = ['CHI', 'UIST', 'CSCW']
        
        # here the year is NOT when a paper was published but when it was cited
        start_year = 2010 + FIRST_N
        num_years = 2022 - start_year # until 2022

        for dyear in range(0, num_years + 1):
            cite_year = start_year + dyear
            cite_years.append(cite_year)
        
        # !!! DO NOT DELETE
        # >>> for showing absolute counts
        # titles = {
        #     'non-hci-citations-distr-by-cite-year': 'non-HCI citations',
        #     'hci-citations-distr-by-cite-year': 'HCI citations'
        # }

        # for key in titles:
        d1 = {} # non-HCI
        d2 = {} # HCI
        d1['year'] = cite_years
        d2['year'] = cite_years
        for venue in venues:

            d1[venue] = [0] * (num_years + 1)
            d2[venue] = [0] * (num_years + 1)

            for venue_year in results:
                if venue not in venue_year:
                    continue

                distr_by_cite_year_hci_citations = results[venue_year]['hci-citations-distr-by-cite-year']
                distr_by_cite_year_non_hci_citations = results[venue_year]['non-hci-citations-distr-by-cite-year']
                
                this_year = int(venue_year[-4:])
                # for each year of citations
                for dyear in range(0, num_years + 1):
                    cite_year = start_year + dyear
                    
                    # if this citation year is too far away from the paper's publishing year, don't include it
                    if cite_year - this_year > FIRST_N:
                        continue
                    
                    if str(cite_year) in distr_by_cite_year_non_hci_citations:
                        d1[venue][dyear] += distr_by_cite_year_non_hci_citations[str(cite_year)]
                    if str(cite_year) in distr_by_cite_year_hci_citations:
                        d2[venue][dyear] += distr_by_cite_year_hci_citations[str(cite_year)]
            
            # !!! DO NOT DELETE
            # >>> normalization if you want to show abs counts
            # 
            # for dyear in range(0, num_years):
            #     year = start_year + dyear
            #     cnt = 0
            #     for prev_year in range(year - FIRST_N, year + 1):
            #         venue_year = venue + str(prev_year)
            #         if venue_year in paper_counts:
            #             cnt += int(paper_counts[venue_year])
            #         else:
            #             d[venue][dyear] = float('NaN')
            #     d[venue][dyear] /= cnt

            for dyear in range(0, num_years + 1):
                # d1 becomes x-index
                d1[venue][dyear] /= (d1[venue][dyear] + d2[venue][dyear])

        df = pd.DataFrame(data=d1)
        fig = px.line(df, x='year', y=venues, title="Each year's X-index only based on HCI papers published in the previous " + str(FIRST_N) + " years")
        fig.update_layout(yaxis=dict(range=[0, 1]))
        if DEBUG:
            fig.show()
        pio.write_image(fig, os.path.join(DIR_OUTPUT_IMAGES,'fig4.png'), width=WIDTH_FIG, height=HEIGHT_FIG)

    
    plot_measurement_1()
    plot_measurement_2()
    plot_measurement_3()
    plot_measurement_4()