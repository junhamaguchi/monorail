"""
画像認識用モノレール模型制御プログラム
Raspberry Pi Picoを使用したWeb制御可能なモノレール模型システム

機能:
- 超音波距離センサーによる障害物検知
- Webブラウザからのモーター速度制御
- 自動停止機能（障害物検知時）
- Wi-Fi経由でのリモート制御
"""

import sys
import _thread
from machine import Pin, time_pulse_us
import network
import socket
import time
import PicoMotorDriver

# 内蔵LED（システム状態表示用）
led = Pin("LED", Pin.OUT)

# 超音波距離センサー（HC-SR04）のピン設定
trigger = Pin(27, Pin.OUT)  # トリガーピン（出力）
echo    = Pin(26, Pin.IN)   # エコーピン（入力）

# Wi-Fi設定（環境に応じて変更）
#ssid = 'Buffalo-G-2B3E'
#password = '5k8ud3revnvfu'
#ssid = 'TP-Link_860E'
#password = '81113927'
ssid = 'SH-54Ca-9D339D'
password = 'kg4Rfjzp0a'

# Wi-Fi接続設定
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# モータードライバーボードの初期化
board = PicoMotorDriver.KitronikPicoMotor()

# モーター速度変数（0-100%）
speed = 0

# Wi-Fi接続待機
while not wlan.isconnected():
    print("Wi-Fi Connecting...")
    time.sleep(1)

# 接続成功時のIPアドレス表示
ip = wlan.ifconfig()[0]
print('Connect IP:', ip)

def get_distance():
    """
    超音波距離センサーから距離を測定する関数
    
    Returns:
        float: 距離（cm）、エラー時はNone
    """
    # トリガーパルスの発生（10μsのパルス）
    trigger.low()            
    time.sleep_us(2)
    trigger.high()
    time.sleep_us(10)
    trigger.low()

    # エコーパルスの測定（最大30ms待機）
    pulse_time = time_pulse_us(echo, 1, 30000)

    if pulse_time < 0:
        return None

    # 距離への変換（音速340m/sを使用）
    distance_cm = (pulse_time / 2) * 0.0343
    return distance_cm


# Web制御用HTMLページ（モーター制御ボタン付き）
html = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { text-align:center; font-family:sans-serif; }
    button {
      width: 80%%; padding: 20px; font-size: 20px; margin: 10px;
      border-radius: 10px; border: none;
    }
    .on100{ background: green; color: white; }
    .on90{ background: green; color: white; }
    .on80{ background: green; color: white; }
    .on70{ background: green; color: white; }
    .off { background: Glay; color: Black; }
  </style>
</head>
<body>
  <h1>Motor Control</h1>
  <form action="/Motor/on1"><button class="on100">Motor ON 1</button></form>
  <form action="/Motor/on2"><button class="on90">Motor ON 2</button></form>
  <form action="/Motor/on3"><button class="on80">Motor ON 3</button></form>
  <form action="/Motor/on4"><button class="on70">Motor ON 4</button></form>
  <form action="/Motor/on5"><button class="on70">Motor ON 5</button></form>
  <form action="/Motor/off"><button class="off">Motor OFF</button></form>
  </br></br></br></br>
</body>
</html>
"""

# Webサーバー起動（ポート80）
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(1)
print('Web Server Running... http://%s' % ip)

# システム稼働を示すLED点灯
led.value(1)

def main():
    """
    メイン関数：Webサーバー処理とリクエスト解析
    """
    global speed

    while True:
        # クライアント接続待機
        conn, addr = server.accept()
        print('接続:', addr)
        request = conn.recv(1024)
        request_str = request.decode()
        
        request_line = request_str.split('\n')[0]
        print("Request：", request_line)

        # Webリクエストに基づくモーター速度制御
        if 'GET /Motor/on1' in request_line:
            speed = 100  # 最大速度
        elif 'GET /Motor/on2' in request_line:
            speed = 90   # 90%速度
        elif 'GET /Motor/on3' in request_line:
            speed = 80   # 80%速度
        elif 'GET /Motor/on4' in request_line:
            speed = 70   # 70%速度
        elif 'GET /Motor/on5' in request_line:
            speed = 60   # 60%速度
        elif 'GET /Motor/off' in request_line:
            speed = 0    # 停止

        # HTMLレスポンス送信
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(html)
        conn.close()

def Motor():
    """
    モーター制御関数：距離センサーによる自動停止機能付き
    別スレッドで実行され、継続的にモーターとセンサーを監視
    """
    global speed
    global board

    step = 0  # 停止状態管理（0:通常走行, 1:停止中, 2:再開待機）

    while True:
        speed_new = speed

        # 距離センサーによる障害物検知
        dist = get_distance()
        if dist is None:
            print("Distance sensor error")
        else:
            print("Length: {:.2f} cm".format(dist))
            
            # 障害物検知時の自動停止ロジック
            if speed_new > 0 and dist < 10.0 and step == 0:
                step = 1  # 停止状態へ移行
            if speed_new > 0 and dist > 30.0 and step == 2:
                step = 0  # 通常走行状態へ復帰

        # 停止状態の処理
        if step == 1:
            speed_new = 0  # モーター停止

        # モーター制御実行
        if speed_new > 0:
            board.motorOn(1, 'f', speed_new)  # 前進
        else:
            board.motorOff(1)  # 停止
        
        # 停止後の再開待機時間
        if step == 1:
            time.sleep(2)  # 2秒間停止
            step = 2       # 再開待機状態へ

        time.sleep(0.05)  # 50ms間隔でループ

if __name__ == '__main__':
    # モーター制御を別スレッドで開始
    _thread.start_new_thread(Motor, ())
    # メインスレッドでWebサーバーを開始
    main()
