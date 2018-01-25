# 통신 프로그램
# 제어에서 받은 정보로 통신 패킷 만들어서 플랫폼으로 보내기
# 플랫폼에서 통신 패킷 받아와서 제어로 보내기
# 패킷 세부 형식(string)은 책자 참조
# input: (from car_control)
# output: (to car_control)

import serial
import time
import math

# CONSTANT for _read()
DISTANCE_PER_ROTATION = 54.02 * math.pi  # Distance per Rotation [cm]
PULSE_PER_ROTATION = 100.  # Pulse per Rotation
DISTANCE_PER_PULSE = DISTANCE_PER_ROTATION / PULSE_PER_ROTATION  # Distance per Pulse

class PlatformSerial:
    def __init__(self, platform_port):
        self.platform = platform_port
        # 포트 오픈
        try:
            self.ser = serial.Serial(self.platform, 115200)  # Baud rate such as 9600 or 115200 etc.
        except Exception as e:
            print(e)

        # 쓰기 데이터 셋
        self.writing_data = bytearray()

    def _read(self):  # read data from platform
        reading_data = bytearray(self.ser.readline())  # byte array 로 읽어옴
        self.reading_data = reading_data
        try:
            # data parsing, 패킷 설명은 책자 참조
            ETX1 = reading_data[17]
            AorM = reading_data[3]
            ESTOP = reading_data[4]
            GEAR = reading_data[5]
            SPEED = reading_data[6] + reading_data[7] * 256
            STEER = reading_data[8] + reading_data[9] * 256

            # STEER 범위 조정
            if STEER >= 32768:  # 65536 / 2 = 32768
                STEER = 65536 - STEER
            else:
                STEER = -STEER

            BRAKE = reading_data[10]
            time_encoder = time.time()

            # ENC0, ENC1, ENC2, ENC3
            ENC = reading_data[11] + reading_data[12] * 256 + reading_data[13] * 65536 + reading_data[14] * 16777216
            if ENC >= 2147483648:
                ENC = ENC - 4294967296

            ALIVE = reading_data[15]

            try:
                speed_from_encoder = (ENC - self.ENC1[0]) * DISTANCE_PER_PULSE / (time_encoder - self.ENC1[1]) * 0.036
                print('STEER = ', STEER, ' SPEED_ENC = ', speed_from_encoder)
            except Exception as e:
                print(e)
                pass

            self.ENC1 = (ENC, time_encoder)

        except:
            pass

    def _write(self, speed_for_write, steer_for_write, brake_for_write):  # write data to platform
        dummy_data = bytearray()
        try:
            steer_for_write = int(steer_for_write * 1.015)

            if steer_for_write < 0:
                steer_for_write = steer_for_write + 65536
            dummy_data[6] = 0
            print("steer_for_write = ", steer_for_write, "/ speed_for_write = ", speed_for_write, "/ BRAKE = ", brake_for_write)
            dummy_data[7] = speed_for_write
            # 16진법 두 칸 전송
            dummy_data[8] = steer_for_write / 256
            dummy_data[9] = steer_for_write % 256

            self.writing_data[3] = 1
            self.writing_data[4] = 0  # E stop
            self.writing_data[5] = 0

            # 임시 데이터를 최종 데이터에 입력
            self.writing_data[6] = dummy_data[6]
            self.writing_data[7] = dummy_data[7]
            self.writing_data[8] = dummy_data[8]
            self.writing_data[9] = dummy_data[9]
            self.writing_data[10] = brake_for_write

            # 받은 데이터와 똑같이 전송, 플랫폼 자체적으로 데이터 수신 간격을 알기 위함
            self.writing_data[11] = self.reading_data[15]
            self.writing_data[12] = self.reading_data[16]
            self.writing_data[13] = self.reading_data[17]

            self.ser.write(str(self.writing_data))

        except Exception as e:
            print(e)
            print(' auto error')
            self.ser.write(str(self.writing_data))
        pass

    def get_data_real_time(self):
        # _read() 를 이용해 플랫폼 데이터를 실시간으로 읽음
        try:
            while True:
                self._read()
        except KeyboardInterrupt:  # ctrl+C 누르면 탈출
            pass
        self.ser.close()

    def give_data(self, speed, steer, brake):
        # 사용자 입장에서 쓰고자 하는 데이터만 받아서 _write 로 전달
        try:
            while True:
                self._write(speed, steer, brake)
        except KeyboardInterrupt:
            pass
        self.ser.close()


if __name__ == '__main__':
    port = 'COM3'
    # e.g. /dev/ttyUSB0 on GNU/Linux or COM3 on Windows.
    ser_for_platform = PlatformSerial(port)
    ser_for_platform.get_data_real_time()
