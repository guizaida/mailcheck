from logging import exception
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import base64
import email
from bs4 import BeautifulSoup
import requests

#api作用域如不確定可使用:https://mail.google.com/ 獲取不受限制權限,如果有任何變更請刪除token.pickle重新驗證一次
SCOPES = ['https://www.googleapis.com/auth/gmail.modify','https://mail.google.com/']
def getEmails():
    # Variable creds will store the user access token.
    # If no valid token found, we will create one.
    creds = None
    #檢查權限檔案是否已存在
    if os.path.exists('token.pickle'):
        # 如果存在則讀取
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # 如果不存在則會讀取credentials.json 使用他去獲取token.pickle需要的檔案並儲存 這邊會開啟oauth網頁認證
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 儲存token.pickle以方便下次運行讀取,這樣就不需要每次都認證了
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # 建立api連結
    service = build('gmail', 'v1', credentials=creds,)
    # 獲取所有郵件訊息(預設為100則)
    result = service.users().messages().list(userId='a72140959@gmail.com').execute()
    # 如果想獲取更多郵件則可使用maxResults參數,範例如下:
    # result = service.users().messages().list(maxResults=200, userId='me').execute()
    messages = result.get('messages')
    #messages型態為字典,其中包含每個郵件的唯一id
    # 歷遍整個字典
    for msg in messages:
        # 依照郵件id獲取郵件內容
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        # 使用try-except來避免遇到錯誤
        try:
            # 從字典中獲取payload的值
            payload = txt['payload']
            headers = payload['headers']
            # 從header獲取郵件標題以及寄送者
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'From':
                    sender = d['value']
            # email內文有加密,所以必須使用base64進行解碼,由於是中文文件所以需要decode並使用UTF-8格式
            data = payload['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data).decode(encoding='UTF-8',errors='strict')
            # 解密完後需要使用bs4進行解析獲取內文
            # it with BeautifulSoup library
            soup = BeautifulSoup(decoded_data , "lxml")
            body = soup.body()#獲取郵件內文
        except Exception as e:
            print(e)
            pass
        # print 郵件標題以及寄件者
        print("Subject: ", subject)
        print("From: ", sender)
        #使用關鍵字對郵件標題進行搜尋,刪除垃圾郵件
        dellist = ['Uber','扣款通知','登入成功通知','ShopBack','對帳單','Well蛋','Heroku','no-reply','歐付寶','The Google Account Team ','願望清單','Nexus Mods','Dropbox','網路交易安全認證密碼通知函','PressPlay Academy','職場新貴報','Humble','會員好康報','每日帳務訊息通知','Board Game','聲藝','WitsPer智選家','消費彙整通知','Oleg from Luden.io','聯合新聞網',' 泰綜合證券','活動報名','Carrefour 家樂福','Twitter','國泰世華','Microsoft 帳戶小組','The Telerik & Kendo UI Teams at Progress','停機通知','104news','小雞上工','Taco from Trello','享購物ENJOYSHO','有人與你共用了資料夾','有人要求共用','已接受','有人與你共用']
        #使用dellist歷遍所有郵件,找出垃圾訊息將它轉移到垃圾桶
        for d in dellist:
            status = False
            if d in subject  :
                service.users().messages().trash(userId='me', id=msg['id']).execute()
                status = True
            if status != True:
                if d in sender  :
                    service.users().messages().trash(userId='me', id=msg['id']).execute()
                    status = True
            if status:
                message = '已將 {0} 郵件移至垃圾桶 \n 寄件人: {1}'.format(subject,sender)
                print(message)
                sendmessage(message)
            
def sendmessage(message):
    #透過line notify發送通知,避免誤刪重要郵件
    with open ('line_notify_token.txt') as f:
        apikey = f.read()
    headers = {"Authorization": "Bearer " + apikey}
    param = {'message': '\n{0}'.format(message)}
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = param)

if __name__ == '__main__':
    # getEmails()
    sendmessage('')