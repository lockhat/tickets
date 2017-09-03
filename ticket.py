#coding=utf-8

import requests, prettytable, json
import pickle, time, sys, codecs
from datetime import date
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from warnings import simplefilter


simplefilter('ignore', InsecureRequestWarning)
class Stations:
    """
        所有车站名以及对应的缩写简称
        station format::
        {
            name.encode('utf-8').hex(): ['bjb', '北京北', 'VAP', 'beijingbei', 'bjb', '0'],
            ....
        }
    """
    def __init__(self, stations_filename='stations', cert='srca.cert',
        station_names_url=None):
        self.station_names_url = station_names_url or \
            'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'
        self.stations = {}
        fp = open(stations_filename, 'wb+')
        try:
            self.stations = pickle.load(fp)
        except:
            self.update_stations(fp)
        finally:
            fp.close()

    def update_stations(self, fp):
        try:
            response = requests.get(self.station_names_url, verify=False)
        except Exception as e:
            print("Update stations error", e)
            raise
        result = response.text.strip()[:-3].split('@')[1:]
        for r in result:
            item = r.strip().split('|')
            self.stations[item[1].encode('utf-8').hex()] = item
        pickle.dump(self.stations, fp)

    def get_symbol(self, name):
        return self.stations[name.encode('utf-8').hex()][2]


class SearchTrains:
    headers = {
        'Host': 'kyfw.12306.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) Chrome/57',
        'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init'
    }
    def __init__(self, from_station, to_station, train_date=None, purpose_codes='ADULT',
        headers=None):
        try:
            train_date = train_date and date(
                *[int(_) for _ in train_date.split('-')]).strftime('%Y-%m-%d') or \
                str(date.today())
        except:
            print('\033[31m请输入正确的日期格式(YYYY-MM-DD)')
            raise
        self.query = {
            'purpose_codes': purpose_codes,
            'leftTicketDTO_from_station': from_station,
            'leftTicketDTO_to_station': to_station,
            'leftTicketDTO_train_date': train_date
        }
        self.headers = headers or self.headers
        self.trains = []

    def request(self):
        query_url = 'https://kyfw.12306.cn/otn/leftTicket/query'
        query_url += '?leftTicketDTO.train_date={leftTicketDTO_train_date}' \
            '&leftTicketDTO.from_station={leftTicketDTO_from_station}' \
            '&leftTicketDTO.to_station={leftTicketDTO_to_station}' \
            '&purpose_codes={purpose_codes}'.format(**self.query)
        try:
            result = requests.get(query_url, headers=self.headers, verify=False)
        except requests.exceptions.Timeout:
            # request timeout, will try again in 5 seconds
            time.sleep(5)
            self.request()
        else:
            self.parse_train(result)

    def parse_train(self, result):
        """解析返回json"""

        result = json.loads(result.text)
        cr = result['data']['map']
        for result_str in result['data']['result']:
            cm = result_str.split('|')
            cq = {}
            cq['train_no'] = cm[2]
            cq['station_train_code'] = cm[3]
            cq['start_station_telecode'] = cm[4]
            cq['end_station_telecode'] = cm[5]
            cq['from_station_telecode'] = cm[6]
            cq['to_station_telecode'] = cm[7]
            cq['start_time'] = cm[8]
            cq['arrive_time'] = cm[9]
            cq['lishi'] = cm[10]
            cq['canWebBuy'] = cm[11]
            cq['yp_info'] = cm[12]
            cq['start_train_date'] = cm[13]
            cq['train_seat_feature'] = cm[14]
            cq['location_code'] = cm[15]
            cq['from_station_no'] = cm[16]
            cq['to_station_no'] = cm[17]
            cq['is_support_card'] = cm[18]
            cq['controlled_train_flag'] = cm[19]
            cq['gg_num'] = cm[20] if cm[20] else "--"
            cq['gr_num'] = cm[21] if cm[21] else "--"
            cq['qt_num'] = cm[22] if cm[22] else "--"
            cq['rw_num'] = cm[23] if cm[23] else "--"
            cq['rz_num'] = cm[24] if cm[24] else "--"
            cq['tz_num'] = cm[25] if cm[25] else "--"
            cq['wz_num'] = cm[26] if cm[26] else "--"
            cq['yb_num'] = cm[27] if cm[27] else "--"
            cq['yw_num'] = cm[28] if cm[28] else "--"
            cq['yz_num'] = cm[29] if cm[29] else "--"
            cq['ze_num'] = cm[30] if cm[30] else "--"
            cq['zy_num'] = cm[31] if cm[31] else "--"
            cq['swz_num'] = cm[32] if cm[32] else "--"
            cq['yp_ex'] = cm[33]
            cq['seat_types'] = cm[34]
            cq['from_station_name'] = cr[cm[6]]
            cq['to_station_name'] = cr[cm[7]]
            cs = {}
            cs['secretStr'] = cm[0]
            cs['buttonTextInfo'] = cm[1]
            cs['queryLeftNewDTO'] = cq
            self.trains.append(cs)

    def show_result(self):
        table = prettytable.PrettyTable()
        table.field_names = ('车次', '车站', '时间', '历时', '商务座', '特等座',
            '一等座', '二等座', '高级软卧', '软卧', '硬卧', '软座', '硬座', '无座', '其他')

        for train in self.trains:
            item = train['queryLeftNewDTO']
            from_sign = '(始)' if item['start_station_telecode'] == \
                self.query['leftTicketDTO_from_station'] else '(过)'
            to_sign = '(终)' if item['end_station_telecode'] == \
                self.query['leftTicketDTO_to_station'] else '(过)'

            table.add_row([
                item['station_train_code'],
                from_sign + item['from_station_name'],
                item['start_time'],
                item['lishi'],
                item['swz_num'],
                item['tz_num'],
                item['zy_num'],
                item['ze_num'],
                item['gr_num'],
                item['rw_num'],
                item['yw_num'],
                item['rz_num'],
                item['yz_num'],
                item['wz_num'],
                item['qt_num']
            ])
            table.add_row(['', '\033[31m' + to_sign + item['to_station_name'] + \
                '\033[0m'] + ['' for _ in range(13)])
        print(table.get_string())


if __name__ == '__main__':
    import argparse
    parse = argparse.ArgumentParser(description='A command to check tickets status ' \
        'from 12306')
    parse.add_argument('src', metavar='ORIGIN',
        help='the station where you get in')
    parse.add_argument('dest', metavar='DESTINATION',
        help='the destination station where you get off')
    parse.add_argument('date', metavar='DATE',
        help='the time you will go.(YYYY-MM-DD)')
    args = parse.parse_args()
    st = Stations()
    try:
        from_station = st.get_symbol(args.src)
        to_station = st.get_symbol(args.dest)
    except KeyError:
        print('\033[31m请输入正确的车站名')
        raise
    train_date = args.date
    search = SearchTrains(from_station, to_station, train_date)
    search.request()
    search.show_result()