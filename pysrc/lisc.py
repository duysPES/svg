import serial
import time
import multiprocessing as mp
from pysrc.errors import ChkSumError, IncorrectPayLoad, ErrorCodes
from pysrc.switch import SwitchManager, Switch
from pysrc.commands import Commands
from pysrc.thread import ConnMode, InfoType, ConnPackage


class LISC(serial.Serial):
    incoming_buffer = []
    switch_manager = SwitchManager()

    def do_inventory(self, queue):
        package = ConnPackage(queue)
        package.debug("Resetting LISC")
        self.reset()
        # response = self.read_serial(lisc)
        for i in range(1):
            response = self.listen()
            # print("Response ", response.hex())

            switch = Switch(position=i, raw=response)
            package.switch(switch)
            self.switch_manager.add(switch)

            package.debug("Getting Status of :{}".format(switch.address))
            msg = switch.gen_package(Commands.SendStatus.value)
            self.write(msg)

            response = self.listen()
            # print("Response ", response.hex())
            package.debug(response.hex())
            # queue.put(response)
            # queue.put({"inventory": False})
            package.done()

    def send(self, byte_string):
        """
        Send byte string on connected port
        """
        self.write(byte_string)

    def listen(self, timeout=2):
        now = time.time()
        buf = b""

        while time.time() - now <= timeout:
            in_waiting = self.inWaiting()
            if in_waiting > 0:
                buf += self.read(in_waiting)
                now = time.time()
        return buf

    def parse_response(self, response, expected=None):
        """
        method parses responses from switches ONLY, not LISC itself.
        Therefore ALL switches will begin with it's address. Reject response 
        if payload is less than 4 bytes long addr+chksum
        """

        if len(response) < 4:
            # either corrupt package or LISC response
            return None
        else:
            #perform chksum on data to make sure it matches
            if not self.chksum_ok(response):
                raise ChkSumError()

            raw_address = response[:3]
            address = raw_address.hex()
            payload = response[3:-1]

            if expected != payload and expected is not None:
                raise IncorrectPayLoad

            if not self.switch_manager.switch_exists(address=address):
                num = self.switch_manager.num
                switch = Switch(position=num + 1, raw=raw_address)
                self.switch_manager.add(sw=switch)
            else:
                print("Switch Exists")

            return switch

    def bytearray_to_hex(self, arr):
        return "".join([i.hex() for i in arr])

    def chksum_ok(self, data):
        if not isinstance(data, bytes):
            raise ValueError("Incoming data must be a collection")

        good_data = True

        supplied_chksum = data[-1]
        calculated_chksum = 0

        for idx in range(len(data) - 1):
            calculated_chksum ^= data[idx]

        if calculated_chksum != supplied_chksum:

            print("Checksums do not match: {}/{}".format(
                calculated_chksum, supplied_chksum))
            return not good_data

        return good_data

    def chksum(self, data):
        """
        return a bytes of data with included checksum
        """
        chksum = 0
        if not isinstance(data, bytes):
            data = bytes([data])

        for element in data:
            chksum ^= element

        data += bytes([chksum])

        return data

    def delay(self, seconds):
        start = time.time()

        while time.time() - start <= seconds:
            continue

    def create_command_packet_for(self, switch, cmd, to_bytearray=True):
        # command structure {3byte id}{payload}{chksum}
        packet = switch.raw_address + [cmd.value]
        packet = self.chksum(packet)
        print("Packet: ", packet)
        return bytearray(packet) if to_bytearray is True else packet

    def reset(self):
        self.send(b'zl')
        self.delay(2)
        self.send(b'zL')


if __name__ == "__main__":
    # ser = LISC(port='/dev/ttyUSB0', baudrate=9600, timeout=0)
    # ser.listen()
    # ser.close()
    with LISC(port='/dev/ttyUSB0', baudrate=9600, timeout=1) as lisc:
        print("Connected to :", lisc.portstr)
        # lisc.echo()
        lisc.reset()
        print("LISTENING")
        response = lisc.recieve(timeout=1)
        print("MADE IT HERE")
        print(response, lisc.parse_response(response))
        lisc.workers.wait_for_workers()
        print("DONE WITH MAIN THREAD")
