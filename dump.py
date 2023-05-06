import sys
import requests
import re

if len(sys.argv) != 3:
  print('No qrz.com subscriber dump logbook to adif format.')
  print('Usage: {} <xf_session> <out_adif_file>'.format(sys.argv[0]))
  sys.exit(-1)


class QrzComLogBook:
  logbook_url = 'https://logbook.qrz.com/logbook'
  adif_doc_url = 'https://www.adif.org/303/adif303.htm'
  header_template = {
    'ADIF_VER':'3.0.3',
    'PROGRAMID':'PyQrzComLogBookDump',
    'PROGRAMVERSION':'1.0',
  }
  record_template = {
    'CALL':'', 
    'OPERATOR':'', 
    'BAND':'', 
    'BAND_RX':'', 
    'GRIDSQUARE':'',
    'MY_GRIDSQUARE':'', 
    'COUNTRY':'', 
    'MY_COUNTRY':'', 
    'COMMENT':'', 
    'QSO_DATE':'', 
    'QSO_DATE_OFF':'', 
    'TIME_ON':'', 
    'TIME_OFF':'', 
    'QTH':'', 
    'MY_CITY':'',
    'RX_PWR':'', 
    'TX_PWR':'', 
    'RST_RCVD':'', 
    'RST_SENT':'',
    'FREQ':'', 
    'FREQ_RX':'', 
    'MODE':'', 
    'MY_NAME':'',
    'NAME':'',
    'MODE':'',
  }

  def __init__(self, xf_session):
    self.headers={'Cookie': 'xf_session='+xf_session}
    r = requests.get(QrzComLogBook.logbook_url, headers=self.headers)
    inp = re.findall(r'<input.*name="(.*?)".*value="(.*?)".*?/>', r.text)
    inp = dict(inp)
    qso_s = re.findall(r'<span class=\'getlist-total_cnt\'>(.*?)</span>', r.text)
    self.qhash = inp['qhash']
    self.bookid = inp['bookid']
    self.qso_s = int(qso_s[0])
    

  def ReadQsoHtml(self, logpos):
    data = {
     'frm':'6',
     'sbook':'0',
     'op':'show',
     'qhash':self.qhash,
     'dir':'',
     'nocache':'0',
     'bookid':self.bookid,
     'page':'1',
     'currentview':'0',
     'admin':'',
     'set':'',
     'showviewopts':'0',
     'app':'',
     'rpp':'15', # rows per page?
     'addcall':'',
     'ipage':'1',
     'ordertype':'date',
     'search':'',
     'viewtype':'-1',
     'logpos':logpos,
    };
    r = requests.post(QrzComLogBook.logbook_url, data=data, headers=self.headers)
    return r.text

  def ParseHtmlTable(self, html):
    f = re.MULTILINE | re.DOTALL
    r = re.findall(r'<table class=.*?>(.*?)</table>', html, f)
    r = re.findall(r'<tr.*?>(.*?)</tr>', r[0], f)
    rec = []
    CLEANER = re.compile('<.*?>')
    for i in r:
      i = re.findall(r'<t[dh].*?>(.*?)</t[dh]>', i, f)
      i = [re.sub(CLEANER, '', j) for j in i]
      rec.append(i)
    return rec

  def TranslateToAdifTags(self, rec):
    record = QrzComLogBook.record_template
    for i in rec:
      if i[0] == 'QSO Start':
        datetime = i[1].replace('-','').replace(':', '').split(' ')[0:2]
        record['QSO_DATE'] = datetime[0]
        record['TIME_ON'] = datetime[1]
      elif i[0] == 'Station':
        record['CALL'] = i[1]
        record['OPERATOR'] = i[2]
      elif i[0] == 'QTH':
        record['QTH'] = i[1]
        record['MY_CITY'] = i[2]
      elif i[0] == 'Country (DXCC)':
        record['COUNTRY'] = i[1]
        record['MY_COUNTRY'] = i[2]
      elif i[0] == 'Frequency':
        f=i[1].split()
        record['FREQ'] = f[0]
        record['BAND'] = f[2]
        record['MODE'] = i[3]
        f=i[4].split()
        record['FREQ_RX'] = f[0]
        record['BAND_RX'] = f[2]
      elif i[0] == 'Power':
        record['RX_PWR'] = i[1].split()[0]
        record['RST_RCVD'] = i[3]
        record['TX_PWR'] = i[4].split()[0]
        record['RST_SENT'] = i[6]
      elif i[0] == 'Grid':
        record['GRIDSQUARE'] = i[1]
        record['MY_GRIDSQUARE'] = i[4]
      elif i[0] == 'Comments':
        record['COMMENT'] = i[1]
      elif i[0] == 'Op':
        record['NAME'] = i[1]
        record['MY_NAME'] = i[2]
    return record

  def ConvertToAdifFormat(self, d):
    return '\n'.join(['<{}:{}>{}'.format(k,len(v),v) for k,v in d.items() if len(v)>0])


  def ReadAdif(self):
    adif = 'Generated based on adif documentation from '+self.adif_doc_url+'\n\n'
    adif += self.ConvertToAdifFormat(QrzComLogBook.header_template)+'\n<EOH>\n\n'
    for logpos in range(self.qso_s-1,-1,-1):
      qso = self.ReadQsoHtml(logpos)
      rec = self.ParseHtmlTable(qso)
      d = self.TranslateToAdifTags(rec)
      a = self.ConvertToAdifFormat(d)+'\n<EOR>\n\n'
      adif += a
      sys.stderr.write(a.replace('\n','')+'\n\n')
    return adif
   

qrz = QrzComLogBook(sys.argv[1])
with open(sys.argv[2], 'w') as f:
  f.write(qrz.ReadAdif())

