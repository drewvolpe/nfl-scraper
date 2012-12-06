
import csv
from datetime import datetime
from bs4 import BeautifulSoup
import re
import urllib

covers_url = 'http://www.covers.com/odds/football/nfl-moneyline-odds.aspx'

def node_to_int(node):
    num_str = re.findall('[-\d]+', node.get_text())[0]
    return int(num_str)

html = urllib.urlopen(covers_url).read()
soup = BeautifulSoup(html)

moneyline_trs = soup.find_all('tr', 'bg_row')

filename = 'lines_%s.csv' % datetime.now().strftime('%Y-%m-%d_%H%M')
rows = []
for tr in moneyline_trs:
    team_away = tr.find('div', 'team_away').find('strong').get_text().strip()
    team_home = tr.find('div', 'team_home').find('strong').get_text().strip()

    # validate team names look right
    if not team_home.startswith('@'):
        raise Exception('Home team "[%s]" did not start with @!!!' % team_home)

    # away team should be listed first
    if html.find(team_away) > html.find(team_home):
        raise Exception('%s appears after %s' % (team_away, team_home))

    line_away = node_to_int(tr.find('div', 'line_top'))
    line_home = node_to_int(tr.find('div', 'covers_bottom'))

    print '%s (%s) is hosting %s (%s)' % (team_home, line_home, team_away, line_away)
    if line_home < line_away:
        favorite = team_home
        favorite_line = line_home
        underdog = team_away
    else:
        favorite = team_away
        favorite_line = line_away
        underdog = team_home

    # line, favorite, opponent
    rows.append([favorite_line, favorite, underdog])

rows = sorted(rows, key=lambda r: r[0])  # sort by line

print 'Got lines for %s games ' % len(rows)

with open(filename, 'wb') as out:
    writer = csv.writer(out, delimiter='\t')
    writer.writerow(['line', 'favorite', 'underdog'])
    for row in rows:
        writer.writerow(row)

print 'Wrote %s' % filename
