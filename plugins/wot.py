#!/usr/bin/python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
#                                                                             #
#    Plugin for iSida Jabber Bot                                              #
#    Copyright (C) 2013 VitaliyS <hetleven@yandex.ua>                         #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
# --------------------------------------------------------------------------- #

import wgpapi

wot_api = wgpapi.Session(getattr(wgpapi.Server, GT('wot_region')), GT('wot_appid'), GT('wot_retries'), GT('wot_delay'))

clantags = re.compile('(\(.*?\))|(\[.*?\])')

def get_tanks_data():
	d = wot_api.fetch('wot/encyclopedia/tanks', 'fields=level,name_i18n,name')
	res = {}
	for i in d:
		n18 = d[i]['name_i18n'].rsplit(':', 1)[-1].replace('_', ' ')
		n = d[i]['name'].rsplit(':', 1)[-1].replace('_', ' ')
		res[i] = {'name_i18n': n18, 'name': n, 'level': d[i]['level']}
	return res

try:
	tanks_data = get_tanks_data()
except:
	tanks_data = {}

def wot(type, jid, nick, text):
	text = text.strip()
	if not text:
		tmp_text = clantags.sub('', nick).strip().split(' ', 1)[0]
		if re.match('[\da-zA-Z_].*?', tmp_text):
			text = tmp_text
	if text:
		text = text.split(' ', 1)
		if len(text) == 1:
			name, tank = text[0], ''
		else:
			name, tank = text[0], text[1].lower()
		
		try: 
			
			v = wot_api.fetch('wot/account/list', 'search=%s&fields=account_id&limit=1' % name)
			player_id = str(v[0]['account_id'])

			vdata = wot_api.fetch('wot/tanks/stats', 'account_id=%s' % player_id)

			pdata = wot_api.fetch('wot/account/info', 'account_id=%s&fields=nickname,statistics,global_rating' % player_id)
			stat = pdata[player_id]['statistics']

			claninfo = wot_api.fetch('wot/clan/membersinfo', 'member_id=%s' % player_id)

			if claninfo[player_id]:
				clan_id = str(claninfo[player_id]['clan_id'])
				cdata = wot_api.fetch('wot/clan/info', 'clan_id=%s&fields=abbreviation' % clan_id)
				cname = cdata[clan_id]['abbreviation']
		except:
			pdata = None

		if pdata and pdata[player_id]:
			wotname = pdata[player_id]['nickname'] + ('[%s]' % cname if claninfo[player_id] else '')

			if tank:
				if len(tank) == 1:
					msg = L('Use more characters in the name of the tank','%s/%s'%(jid,nick))
				else:
					try:
						msg = '%s:' % wotname
						tids = [tid for tid in tanks_data if tank in tanks_data[tid]['name'].lower() or tank in tanks_data[tid]['name_i18n'].lower()]

						for t in vdata[player_id]:
							if str(t['tank_id']) in tids:
								tank_win = t['all']['wins']
								tank_battle = t['all']['battles']
								if tank_battle:
									tank_avgxp = t['all']['battle_avg_xp']
									tank_maxxp = t['max_xp']
									mom = [	L('none','%s/%s'%(jid,nick)),
										L('3 class','%s/%s'%(jid,nick)),
										L('2 class','%s/%s'%(jid,nick)),									L('1 class','%s/%s'%(jid,nick)),
										L('master','%s/%s'%(jid,nick))][t['mark_of_mastery']]
									tank_dmg = int(round(t['all']['damage_dealt'] / float(tank_battle), 0))
									tank_name = tanks_data[str(t['tank_id'])]['name_i18n']
									tank_wins = round(100.0*tank_win/tank_battle, 2)
									msg += L('\n%s: %s/%s (%s%%), avg.damage: %s, xp (avg/max): %s/%s, mastery: %s','%s/%s'%(jid,nick)) % (tank_name, tank_win, tank_battle, tank_wins, tank_dmg, tank_avgxp, tank_maxxp, mom)
								else:
									msg += '\n%s (%s/%s)' % (tanks_data[str(t['tank_id'])]['name_i18n'], tank_win, tank_battle)
						if not msg.count('\n'):
							msg += L(' not founded tank','%s/%s'%(jid,nick))
					except:
						msg = L('Impossible to get tanks\' statistics','%s/%s'%(jid,nick))
			else:

				wins = stat['all']['wins']
				battles = stat['all']['battles']

				if not battles:
					msg = '%s: %s/%s' % (wotname, wins, battles)

				else:
					try:
						win_percent = round(100.0 * wins / battles, 2)
						msg = '%s: %s/%s  (%s%%)' % (wotname, wins, battles, win_percent)

						np = int(win_percent) + 1
						np_int = int((np * battles - 100 * wins) / (100 - np) + 1)
						np05 = int(win_percent + 0.5) + 0.5
						np_round = int((np05 * battles - 100 * wins) / (100 - np05) + 1)

						msg += L('\nUp to %s%% win left: %s battles', '%s/%s'%(jid,nick)) % (np, np_int)
						msg += L('\nUp to %s%% win left: %s battles', '%s/%s'%(jid,nick)) % (np05, np_round)

						avg_exp = stat['all']['battle_avg_xp']

						DAMAGE = stat['all']['damage_dealt'] / float(battles)
						msg += L('\nAv. damage: %s','%s/%s'%(jid,nick)) % int(round(DAMAGE))
						FRAGS = stat['all']['frags'] / float(battles)
						msg += L('\nAv. destroyed: %s','%s/%s'%(jid,nick)) % round(FRAGS, 2)
						SPOT = stat['all']['spotted'] / float(battles)
						msg += L('\nAv. spotted: %s','%s/%s'%(jid,nick)) % round(SPOT, 2)
						CAP = stat['all']['capture_points'] / float(battles)
						msg += L('\nAv. captured points: %s','%s/%s'%(jid,nick)) % round(CAP, 2)
						DEF = stat['all']['dropped_capture_points'] / float(battles)
						msg += L('\nAv. defense points: %s','%s/%s'%(jid,nick)) % round(DEF, 2)
						tanks = [vh for vh in vdata[player_id] if vh['all']['battles']]
						s = sum([t['all']['battles'] * tanks_data[str(t['tank_id'])]['level'] for t in tanks])
						TIER = s / float(battles)
						WINRATE = wins / float(battles)
						msg += L('\nAv. tank lvl: %s','%s/%s'%(jid,nick)) % round(TIER, 2)

						er = DAMAGE * (10 / (TIER + 2)) * (0.23 + 2 * TIER / 100) + FRAGS * 250 + SPOT * 150 + math.log(CAP + 1) / math.log(1.732) * 150 + DEF * 150
						if er < 350:
							er_xvm = 0
						else:
							er_xvm = max(min(er*(er*(er*(er*(er*(3.388e-17*er - 2.469e-13) + 6.9335e-10) - 9.5342e-7) + 6.656e-4) -0.1485) - 0.85, 100), 0)

						msg += L('\nEfficiency rating: %s (XVM: %s)','%s/%s'%(jid,nick)) % (int(round(er)), round(er_xvm, 1))

						if er < 610:
							msg += L(' - bad player','%s/%s'%(jid,nick))
						elif er < 850:
							msg += L(' - player below average','%s/%s'%(jid,nick))
						elif er < 1145:
							msg += L(' - average player','%s/%s'%(jid,nick))
						elif er < 1475:
							msg += L(' - good player','%s/%s'%(jid,nick))
						elif er < 1775:
							msg += L(' - great player','%s/%s'%(jid,nick))
						elif er >= 1775:
							msg += L(' - unicum','%s/%s'%(jid,nick))

						wn6 = (1240 - 1040 / math.pow((min(TIER, 6)), 0.164)) * FRAGS + DAMAGE * 530 / (184 * math.exp(0.24 * TIER) + 130) + SPOT * 125 + min(DEF, 2.2) * 100 + ((185 / (0.17 + math.exp((WINRATE * 100 - 35) * -0.134))) - 500) * 0.45 + (6 - min(TIER, 6)) * (-60)

						if wn6 > 2300:
							wn6_xvm = 100
						else:
							wn6_xvm = max(min(wn6*(wn6*(wn6*(wn6*(wn6*(4.66e-18*wn6 - 3.2413e-14) + 7.524e-11) - 6.516e-8) + 1.307e-5) + 5.153e-2) - 3.9, 100), 0)

						msg += L('\nWN6 rating: %s (XVM: %s)','%s/%s'%(jid,nick)) % (int(round(wn6)), round(wn6_xvm, 1))

						if wn6 < 410:
							msg += L(' - bad player','%s/%s'%(jid,nick))
						elif wn6 < 795:
							msg += L(' - player below average','%s/%s'%(jid,nick))
						elif wn6 < 1185:
							msg += L(' - average player','%s/%s'%(jid,nick))
						elif wn6 < 1585:
							msg += L(' - good player','%s/%s'%(jid,nick))
						elif wn6 < 1925:
							msg += L(' - great player','%s/%s'%(jid,nick))
						elif wn6 >= 1925:
							msg += L(' - unicum','%s/%s'%(jid,nick))

						msg += L('\nWG rating: %s','%s/%s'%(jid,nick)) % pdata[player_id]['global_rating']

						stat_rnd = lambda x: stat['all'][x] - stat['clan'][x] - stat['company'][x]

						armor = math.log(stat_rnd('battles')) / 10 * (stat_rnd('xp')/float(stat_rnd('battles')) + stat_rnd('damage_dealt')/float(stat_rnd('battles')) * (stat_rnd('wins') * 2 + stat_rnd('frags') * 0.9 + (stat_rnd('spotted') + stat_rnd('capture_points') + stat_rnd('dropped_capture_points')) * 0.5)/float(stat_rnd('battles')))

						msg += L('\nArmor-rating: %s','%s/%s'%(jid,nick)) % int(round(armor))

						try:
							data = load_page('http://armor.kiev.ua/wot/api.php?version=iSida3')
							armor_limits = json.loads(data)

							if armor > armor_limits['classRatings']['cv']:
								msg += L(' - virtuoso','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['cm']:
								msg += L(' - master tanker','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['c1']:
								msg += L(' - tanker 1st class','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['c2']:
								msg += L(' - tanker 2nd class','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['c3']:
								msg += L(' - tanker 3rd class','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['d3']:
								msg += L(' - deerhead 3rd class','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['d2']:
								msg += L(' - deerhead 2nd class','%s/%s'%(jid,nick))
							elif armor > armor_limits['classRatings']['d1']:
								msg += L(' - deerhead 1st class','%s/%s'%(jid,nick))
							else: #['dm']
								msg += L(' - master deerhead','%s/%s'%(jid,nick))
						except:
							pass

					except:
						msg = L('Impossible to get statistics','%s/%s'%(jid,nick))
		elif not pdata['status']:
			msg = L('Query error','%s/%s'%(jid,nick))
		else:
			msg = L('Player not found','%s/%s'%(jid,nick))
	else:
		msg = L('What?','%s/%s'%(jid,nick))
	send_msg(type,jid,nick,msg)

def wotclan(type, jid, nick, text):
	text = text.strip().upper()
	if text:
		try:
			data = wot_api.fetch('wot/clan/list/', 'search=%s' % text) 
			claninfo = [i for i in data if i['abbreviation'] == text]
			if claninfo:
				claninfo = claninfo[0]
				clid = claninfo['clan_id']
				owner = claninfo['owner_name']
				created_at = claninfo['created_at']
				abbrev = claninfo['abbreviation']
				data = wot_api.fetch('wot/clan/info/', 'clan_id=%s' % clid) 
				claninfo2 = data[str(clid)]
				msg = L('Name: %s [%s]','%s/%s'%(jid,nick)) % (claninfo2['name'], abbrev)
				msg += L('\nOwner: %s','%s/%s'%(jid,nick)) % owner
				msg += L('\nCreated at: %s','%s/%s'%(jid,nick)) % time.ctime(created_at)
				msg += L('\nCount of members: %s','%s/%s'%(jid,nick)) % claninfo2['members_count']
				msg += L('\nMotto: %s','%s/%s'%(jid,nick)) % claninfo2['motto']
				msg += '\n%s' % claninfo2['description']
			else:
				msg = L('Clan not found','%s/%s'%(jid,nick))
		except:
			msg = L('Impossible to get info','%s/%s'%(jid,nick))
	else:
		msg = L('What?','%s/%s'%(jid,nick))
	send_msg(type,jid,nick,msg)

global execute

execute = [(3, 'wot', wot, 2, 'World of Tanks - info about user. Usage: wot [nick [tank]]'),
			(3, 'wotclan', wotclan, 2, 'World of Tanks - info about clan. Usage: wotclan clan')]
