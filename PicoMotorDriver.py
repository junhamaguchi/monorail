"""
Kitronik Pico Motor Driver Library
Raspberry Pi Pico用のモータードライバー制御ライブラリ

対応機能:
- DCモーター制御（速度・方向制御）
- ステッピングモーター制御
- PWM制御による速度調整
"""

import machine
import utime

class KitronikPicoMotor:
    """
    Kitronik Pico Motor Driver制御クラス
    
    ピン配置:
    - モーター1: ピン4, 5
    - モーター2: ピン9, 10
    
    方向制御:
    - 前進: P5/P9をHIGH、P4/P10をLOW
    - 後退: P4/P10をHIGH、P5/P9をLOW
    """
    
    def motorOn(self, motor, direction, speed):
        """
        DCモーターを指定した方向・速度で動作させる
        
        Args:
            motor (int): モーター番号（1または2）
            direction (str): 方向（'f':前進, 'r':後退）
            speed (int): 速度（0-100%）
        """
        # 速度を0-100%の範囲に制限
        if (speed < 0):
            speed = 0
        elif (speed > 100):
            speed = 100
            
        # 0-100%を0-65535のPWM値に変換
        PWM = int(speed * 655.35)
        
        if motor == 1:
            if direction == "f":
                self.motor1Forward.duty_u16(PWM)
                self.motor1Reverse.duty_u16(0)
            elif direction == "r":
                self.motor1Forward.duty_u16(0)
                self.motor1Reverse.duty_u16(PWM)
            else:
                raise Exception("INVALID DIRECTION")
        elif motor == 2:
            if direction == "f":
                self.motor2Forward.duty_u16(PWM)
                self.motor2Reverse.duty_u16(0)
            elif direction == "r":
                self.motor2Forward.duty_u16(0)
                self.motor2Reverse.duty_u16(PWM)
            else:
                raise Exception("INVALID DIRECTION")
        else:
            raise Exception("INVALID MOTOR")
    
    def motorOff(self, motor):
        """
        モーターを停止させる
        
        Args:
            motor (int): モーター番号（1または2）
        """
        self.motorOn(motor, "f", 0)
        
    #################
    # ステッピングモーター制御
    #################
    # 基本的なフルステップ制御
    # 速度はパルス幅で制御（20msが最速、2000msが最遅）
    # モーター1: PCB端子1,2、モーター2: PCB端子3,4

    def step(self, direction, steps, speed=20, holdPosition=False):
        """
        ステッピングモーターを指定ステップ数動作させる
        
        Args:
            direction (str): 方向（'f':前進, 'r':後退）
            steps (int): ステップ数
            speed (int): パルス幅（ms）
            holdPosition (bool): 位置保持するかどうか
        """
        if(direction == "f"):
            directions = ["f", "r"]
            coils = [1, 2]
        elif (direction == "r"):
            directions = ["r", "f"]
            coils = [2, 1]
        else:
            raise Exception("INVALID DIRECTION")
            
        while steps > 0: 
            for direction in directions:
                if(steps == 0):
                    break
                for coil in coils:
                    self.motorOn(coil, direction, 100)
                    utime.sleep_ms(speed)
                    steps -= 1
                    if(steps == 0):
                        break
                        
        # 電力節約のため位置保持しない場合はコイルをオフ
        if(holdPosition == False):            
            for coil in coils:
                self.motorOff(coil)

    def stepAngle(self, direction, angle, speed=20, holdPosition=False, stepsPerRev=200):
        """
        ステッピングモーターを指定角度動作させる
        
        Args:
            direction (str): 方向（'f':前進, 'r':後退）
            angle (float): 角度（度）
            speed (int): パルス幅（ms）
            holdPosition (bool): 位置保持するかどうか
            stepsPerRev (int): 1回転あたりのステップ数
        """
        # 角度をステップ数に変換
        steps = int(angle / (360 / stepsPerRev))
        print(steps)
        self.step(direction, steps, speed, holdPosition)
        
    def __init__(self, Motor1ForwardPin=machine.Pin(3), Motor1ReversePin=machine.Pin(2), 
                 Motor2ForwardPin=machine.Pin(6), Motor2ReversePin=machine.Pin(7), 
                 PWMFreq=10000):
        """
        モータードライバーの初期化
        
        Args:
            Motor1ForwardPin: モーター1前進ピン
            Motor1ReversePin: モーター1後退ピン
            Motor2ForwardPin: モーター2前進ピン
            Motor2ReversePin: モーター2後退ピン
            PWMFreq (int): PWM周波数（Hz）
        """
        # PWMオブジェクトの作成
        self.motor1Forward = machine.PWM(Motor1ForwardPin)
        self.motor1Reverse = machine.PWM(Motor1ReversePin)
        self.motor2Forward = machine.PWM(Motor2ForwardPin)
        self.motor2Reverse = machine.PWM(Motor2ReversePin)
        
        # PWM周波数の設定
        self.motor1Forward.freq(PWMFreq)
        self.motor1Reverse.freq(PWMFreq)
        self.motor2Forward.freq(PWMFreq)
        self.motor2Reverse.freq(PWMFreq)

         
