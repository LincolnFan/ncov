# encoding=utf-8
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.utils import formataddr
import json, copy, requests, time, re, smtplib
import schedule
my_sender = '2543603118@qq.com'  # 发件人邮箱账号
my_pass = 'tjcakmejjqjmeafj'  # 发件人邮箱授权码

# 当今日没有填报时，在https://app.bupt.edu.cn/ncov/wap/default/index下进行填报，
# 全部填完，不要提交，f12打开控制台，在Console页面下输入代码 console.log(vm.info) 就会得到以下信息，之后每天就默认填以下信息

INFO = r"""{
        "address":"北京市海淀区北太平庄街道北京邮电大学海淀校区",
        "area":"北京市  海淀区",
        "bztcyy":"",
        "city":"北京市",
        "csmjry":"0",
        "fjqszgjdq":"",
        "geo_api_info":"{\"type\":\"complete\",\"position\":{\"Q\":39.960390625,\"R\":116.356397569445,\"lng\":116.356398,\"lat\":39.960391},\"location_type\":\"html5\",\"message\":\"Get ipLocation failed.Get geolocation success.Convert Success.Get address success.\",\"accuracy\":23,\"isConverted\":true,\"status\":1,\"addressComponent\":{\"citycode\":\"010\",\"adcode\":\"110108\",\"businessAreas\":[{\"name\":\"北下关\",\"id\":\"110108\",\"location\":{\"Q\":39.955976,\"R\":116.33873,\"lng\":116.33873,\"lat\":39.955976}},{\"name\":\"西直门\",\"id\":\"110102\",\"location\":{\"Q\":39.942856,\"R\":116.34666099999998,\"lng\":116.346661,\"lat\":39.942856}},{\"name\":\"小西天\",\"id\":\"110108\",\"location\":{\"Q\":39.957147,\"R\":116.364058,\"lng\":116.364058,\"lat\":39.957147}}],\"neighborhoodType\":\"科教文化服务;学校;高等院校\",\"neighborhood\":\"北京邮电大学\",\"building\":\"北京邮电大学计算机学院\",\"buildingType\":\"科教文化服务;学校;高等院校\",\"street\":\"西土城路\",\"streetNumber\":\"10号\",\"country\":\"中国\",\"province\":\"北京市\",\"city\":\"\",\"district\":\"海淀区\",\"township\":\"北太平庄街道\"},\"formattedAddress\":\"北京市海淀区北太平庄街道北京邮电大学计算机学院北京邮电大学海淀校区\",\"roads\":[],\"crosses\":[],\"pois\":[],\"info\":\"SUCCESS\"}",
        "glksrq":"",
        "gllx":"",
        "gtjzzchdfh":"",
        "gtjzzfjsj":"",
        "ismoved":"0",
        "jcbhlx":"",
        "jcbhrq":"",
        "jchbryfs":"",
        "jcjgqr":"0",
        "jcwhryfs":"",
        "jhfjhbcc":"",
        "jhfjjtgj":"",
        "jhfjrq":"",
        "mjry":"0",
        "province":"北京市",
        "qksm":"",
        "remark":"",
        "sfcxtz":"0",
        "sfcxzysx":"0",
        "sfcyglq":"0",
        "sfjcbh":"0",
        "sfjchbry":"0",
        "sfjcwhry":"0",
        "sfjzdezxgym":"1",
        "sfjzxgym":"1",
        "sfsfbh":"0",
        "sftjhb":"0",
        "sftjwh":"0",
        "sfxk":"0",
        "sfygtjzzfj":"",
        "sfyyjc":"0",
        "sfzx":1,
        "szcs":"",
        "szgj":"",
        "szsqsfybl":"0",
        "tw":"2",
        "xjzd":"",
        "xkqq":"",
        "xwxgymjzqk":"3",
        "ymjzxgqk":"已接种",
        "zgfxdq":"0"
        }"""

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "app.bupt.edu.cn",
    "Origin": "https://app.bupt.edu.cn",
    "Referer": "https://app.bupt.edu.cn/uc/wap/login?redirect=https://app.bupt.edu.cn/ncov/wap/default",
    "sec-ch-ua": '''"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"''',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest"
}
# constants
LOGIN_PAGE = "https://auth.bupt.edu.cn/authserver/login" \
             "?service=https%3A%2F%2Fapp.bupt.edu.cn%2Fa_bupt" \
             "%2Fapi%2Fsso%2Fcas%3Fredirect%3Dhttps%253A%252F%252Fapp.bupt.edu.cn" \
             "%252Fncov%252Fwap%252Fdefault%252Findex%26from%3Dwap"
LOGIN_API = 'https://auth.bupt.edu.cn/authserver/login'
GET_API = 'https://app.bupt.edu.cn/ncov/wap/default/index'
REPORT_API = 'https://app.bupt.edu.cn/ncov/wap/default/save'
GETEven_API = 'https://app.bupt.edu.cn/xisuncov/wap/open-report/index'
POSTEven_API = 'https://app.bupt.edu.cn/xisuncov/wap/open-report/save'


def reporter(username, password, use_old):
    # 创建Session对象
    # requests库的session对象会在同一个session实例的所有请求之间使用cookies保持登录状态
    session = requests.Session()
    login_page = session.get(GET_API)
    submit = "登录"
    type = "username_password"
    execution = re.findall('(<input\s*name="execution".*?value=")(.+?)(")', login_page.text)[0][1]
    evenId = re.findall('(<input.*?name="_eventId".*value=")(.+)(")', login_page.text)[0][1]

    # 在session中发送登录请求，此后这个session里就存储了cookie
    login_res = session.post(
        LOGIN_API,
        data={
            'username': username,
            'password': password,
            'submit': submit,
            'type': type,
            'execution': execution,
            '_eventId': evenId
        },
        allow_redirects=True
    )
    if login_res.status_code != 200:
        raise RuntimeError('打卡页面获取失败')

    post_data = json.loads(copy.deepcopy(INFO).replace("\n", "").replace(" ", ""))
    try:
        old_data = json.loads('{' + re.findall(r'(?<=oldInfo: {).+(?=})', login_res.text)[0] + '}')
    except:
        print('获取昨日数据失败，将使用固定打卡数据')
        old_data = {}

    # 如使用
    if old_data and use_old:
        try:
            for k, v in old_data.items():
                if k in post_data:
                    post_data[k] = v
            geo = json.loads(old_data['geo_api_info'])
            province = geo['addressComponent']['province']
            city = geo['addressComponent']['city']
            if geo['addressComponent']['city'].strip() == "" and len(re.findall(r'北京市|上海市|重庆市|天津市', province)) != 0:
                city = geo['addressComponent']['province']
            area = province + " " + city + " " + geo['addressComponent']['district']
            address = geo['formattedAddress']
            post_data['province'] = province
            post_data['city'] = city
            post_data['area'] = area
            post_data['address'] = address
            # 强行覆盖一些字段
            post_data['ismoved'] = 0  # 是否移动了位置？否
            post_data['bztcyy'] = ''  # 不在同城原因？空
            post_data['sfsfbh'] = 0  # 是否省份不合？否
        except:
            print("加载昨日数据错误，采用固定数据")
            post_data = json.loads(copy.deepcopy(INFO).replace("\n", "").replace(" ", ""))

    cov_data = bytes(urllib.parse.urlencode(post_data), encoding='utf8')
    no_cov_report = session.post(REPORT_API, headers=headers, data=cov_data)

    # 携带cookies 以get方式访问目标url
    result_data = no_cov_report.content.decode('UTF-8')
    text = eval(result_data)["m"]
    return text


def mail(my_user, text):
    ret = True
    try:
        msg = MIMEText('每日疫情签到情况：' + text, 'plain', 'utf-8')
        msg['From'] = formataddr(["打卡小助手", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["我的主人", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = "每日疫情签到情况：" + text  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱授权码
        server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
        print(e)
    return ret


def main(users_box):
    use_old = 0
    for [username, password, email_receiver] in users_box:
        result = reporter(username, password, use_old)
        # print(result)
        ret = mail(email_receiver, result)
        if ret:
            print("邮件发送成功")
        else:
            print("邮件发送失败")
        time.sleep(10)


if __name__ == '__main__':
    box = [
        ['2022110304', 'Lincoln7475', 'fanlongjun@bupt.edu.cn']
    ]
    report_time = '01:02'
    schedule.every().day.at(report_time).do(main, box)
    # main(box)
    while True:
        schedule.run_pending()

