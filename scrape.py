
import csv
from datetime import datetime
from bs4 import BeautifulSoup
import re
import urllib

covers_moneyline_url = 'http://www.covers.com/odds/football/nfl-moneyline-odds.aspx'
covers_standings_url = 'http://www.covers.com/pageLoader/pageLoader.aspx?page=/data/nfl/standings/2014-2015/reg/league/standings.html'


def node_to_int(node):
    num_str = re.finditer('[-\d]+', node.get_text()).next().group()
    return int(num_str)


def normalize_team_name(team):
    at_pos = team.find('@')
    if at_pos >= 0:
        team = team[at_pos+1:]
    return team


def get_standings_dict():
    standings_dict = {}
    html = urllib.urlopen(covers_standings_url).read()
    soup = BeautifulSoup(html, "html.parser")
    trs = soup.find_all('tr')
    for tr in trs:
        td_team = tr.find('td', 'datacell')
        if not td_team:
            continue
        team = td_team.find('a').string  # link is team name
        tds = tr.find_all('td', 'datacellc')
        wins = node_to_int(tds[0])
        losses = node_to_int(tds[1])
        ties = node_to_int(tds[2])
        standings_dict[team] = [wins, losses, ties]
    return standings_dict


def get_moneyline_rows():
    html = urllib.urlopen(covers_moneyline_url).read().decode('utf8')
    soup = BeautifulSoup(html, "html.parser")

    moneyline_trs = soup.find_all('tr', 'bg_row')

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
        rows.append({'favorite_line' : favorite_line, 'favorite' : favorite,
                     'underdog' : underdog})

    return sorted(rows, key=lambda r: r['favorite_line'])  # sort by line


if __name__ == "__main__":

    print 'fetching data.'

    standings_dict = get_standings_dict()

    rows = get_moneyline_rows()
    print 'Got lines for %s games ' % len(rows)

    filename = 'lines_%s.csv' % datetime.now().strftime('%Y-%m-%d_%H%M')
    with open(filename, 'wb') as out:
        writer = csv.writer(out, delimiter='\t')
        writer.writerow(['line', 'favorite', 'underdog', 'favorite wins', 'underdog wins',\
                         'win diff'])
        for row in rows:
            favorite_wins = standings_dict[normalize_team_name(row['favorite'])][0]
            underdog_wins = standings_dict[normalize_team_name(row['underdog'])][0]
            win_diff = favorite_wins - underdog_wins
            writer.writerow([row['favorite_line'], row['favorite'], row['underdog'], \
                             favorite_wins, underdog_wins, win_diff])

    print 'Wrote %s' % filename
    print 'done.'
